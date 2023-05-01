import os 
import pickle
import pandas as pd
import numpy as np

# remove 5 lines below and uncomment next 2 lines when CPR package is updated 
import sys
os.path.normpath(os.getcwd() + os.sep + os.pardir)
#sys.path.insert(1, '../CPR')
sys.path.append('/Users/TessaLoRiggio/CEDIA Dropbox/Tessa LoRiggio/RSI/CPR_master_mac2015')
import life
import tools
#from CPR import life
#from CPR import tools

sys.path.append('/Users/TessaLoRiggio/CEDIA Dropbox/Tessa LoRiggio/RSI/srpp_master')
import srpp

sys.path.append('/Users/TessaLoRiggio/CEDIA Dropbox/Tessa LoRiggio/RSI/srd_master')
import srd

module_dir = os.path.dirname(os.path.dirname(__file__))
path_params = '/CPR/data/params/'
path_factors = '/CPR/data/precomputed/'



class CommonParameters:
    """
    This class sets and contains the parameters common to all households.
    
    Parameters
    ----------
    nsim: int
        number of simulations
    non_stochastic: bool
        True if non stochastic simulation, False otherwise
    extra_params: dict
        dictionary of extra parameters
    """
    def __init__(self, nsim, non_stochastic, extra_params):

        self.nsim = nsim
        self.non_stochastic = non_stochastic
        for file in ['common_params.csv', 'user_options.csv', 'prices.csv']:
            tools.add_params_as_attr(self, module_dir + path_params + file)
        tools.change_params(self, extra_params)

        self.tax = srd.tax(year=self.base_year)

        self.rules_cpp = srpp.rules()
        self.rules_qpp = srpp.rules(qpp=True)
        self.gr_rrsp_limit = self.inflation_rate + self.gr_wages
        self.gr_tfsa_limit = self.inflation_rate

        for name in ['rrsp', 'tfsa']:
            self.set_limits(name)

        self.d_ympe = self.prepare_ympe()
        self.d_perc_cpp = self.prepare_cpp()
        self.d_perc_rrif = tools.get_params(
            module_dir + path_params + 'rrif_rates.csv', numerical_key=True)

    def set_limits(self, name):
        """
        Set contributions limits for RRSP and TFSA.

        Parameters
        ----------
        name: str
            RRSP or TFSA
        """
        d = {}
        for year in range(self.base_year, self.base_year + self.future_years):
            try:
                d[year] = getattr(self, f'{name}_limit_{year}')
            except:
                d[year] = round(d[year-1]
                                * (1+getattr(self, f'gr_{name}_limit')))
        setattr(self, f'd_{name}_limit', d)

    def prepare_ympe(self):
        """"
        Pre-reform ympe used to adjust DB benefits for CPP
        """
        d_ympe = tools.get_params(module_dir + path_params + 'ympe.csv',
                                  numerical_key=True)
        for year in range(max(d_ympe.keys()) + 1,
                          self.base_year + self.future_years):
            d_ympe[year] = round(d_ympe[year-1] * (1 + self.gr_ympe))
        return d_ympe

    def prepare_cpp(self):
        """
        Set percentages for cpp/qpp benefits.
        """
        d_perc_cpp = {year: getattr(self, f'perc_cpp_{year}')
                      for year in range(2018, 2023)}
        d_perc_cpp.update(
            {year: self.perc_cpp_2023
             for year in range(2023, self.base_year + self.future_years)})
        return d_perc_cpp


class Prices:
    """
    This class computes the times series for asset returns,
    interest rates on debt, deterministic wage profiles,
    housing price growth rate and price/rent ratio.
    
    Parameters
    ----------
    common: Common
        instance of the class Common
    extra_params: dict
        dictionary of extra parameters
    """
    def __init__(self, common, extra_params):
        tools.add_params_as_attr(self, module_dir + path_params + 'prices.csv')
        tools.change_params(self, extra_params)
        np.random.seed(self.seed)

        for asset in ['bills', 'bonds', 'equity', 'business']:
            ret = self.simulate_ret(asset, common)
            setattr(self, f'ret_{asset}', ret)

        self.ret_housing, self.price_rent_ratio = self.simulate_housing(common)

        self.d_infl_factors = self.prepare_inflation_factors(common)
        self.d_interest_debt = self.simulate_interest_debt()
        self.d_diff_log_wages = self.attach_diff_log_wages()

        if common.recompute_factors:
            self.d_factors = self.initialize_factors()
        else:
            with open(module_dir + path_factors + 'd_factors.pickle', 'rb') as file:
                self.d_factors = pickle.load(file)

    def simulate_ret(self, asset, common):
        """
        Simulate N series of length T nominal returns distributed lognormally
        with autocorrelation rho.

        Parameters
        ----------
        asset: str
            type of asset
        common: Common
            instance of the class Common

        Returns
        -------
        numpy.array:
            Array of nominal returns
        """
        r = np.empty((common.future_years, common.nsim))
        r[0, :] = getattr(self, f'ret_{asset}_2018')
        mu = getattr(self, f'mu_{asset}')
        rho = getattr(self, f'rho_{asset}')
        sigma = getattr(self, f'sig_{asset}')

        alpha, sig_eps = self.compute_params_process(mu, rho, sigma)

        if common.non_stochastic:
            for t in range(1, common.future_years):
                r[t, :] = np.exp(alpha) * (1+r[t-1, :])**rho \
                    * np.exp(sig_eps**2/2) - 1
        else:
            eps = np.random.normal(loc=0, scale=sig_eps,
                                   size=(common.future_years, common.nsim))
            for t in range(1, common.future_years):
                r[t, :] = np.exp(alpha) * (1+r[t-1, :])**rho \
                    * np.exp(eps[t, :]) - 1
        return (1+r) * (1 + self.inflation_rate) - 1

    def compute_params_process(self, mu, rho, sigma):
        """        
        Convert arithmetic mean mu and volatility sigma of the returns
        and autocorrelation rho of the log returns into
        :math:`\\alpha`, :math:`\\rho` and :math:`\\sigma_{\\epsilon}` of the process:
        
        :math:`\\ln(1+r_t) = \\alpha + \\rho * \\ln(1+r_{t-1}) + \\epsilon`,
        where :math:`\\epsilon \\sim N(0, \\sigma_{\\epsilon})`.

        Parameters
        ----------
        mu: float
            arithmetic mean
        rho: float
            autocorrelation :math:
        sigma: float
            standard deviation

        Returns
        -------
        float:
            AR(1) coefficient (:math:`\\alpha`)
        float:
            Standard deviation of error term (:math:`\\sigma_{\\epsilon}`)
        """
        m, v = (1+mu), sigma**2
        sig_lognorm = np.sqrt(np.log(1 + v / m**2))
        mu_lognorm = np.log(m / np.sqrt(1 + v / m**2))
        alpha = (1-rho) * mu_lognorm
        sig_eps = np.sqrt(1 - rho**2) * sig_lognorm
        return alpha, sig_eps

    def simulate_housing(self, common):
        """
        Simulate series of nominal housing price growth (in :math:`\\ln(1+r)` form)
        and price-rent ratio.

        Parameters
        ----------
        common: Common
            instance of the class Common

        Returns
        -------
        numpy.array:
            Array of nominal housing price growth
        numpy.array:
            Array of price-rent ratios
        """
        r = np.empty((common.future_years, common.nsim))
        r[0, :] = self.ret_housing_2018
        rho_r = self.rho_housing
        alpha_r, sig_eps_r = self.compute_params_process(
            self.mu_housing, rho_r, self.sig_housing)

        ratio = np.empty_like(r)
        ratio[0, :] = self.price_rent_2018
        rho_ratio = self.rho_price_rent
        alpha_ratio = self.mu_price_rent * (1 - rho_ratio)
        sig_eps_ratio = np.sqrt(1 - rho_ratio**2) * self.sig_price_rent

        if common.non_stochastic:
            for t in range(1, common.future_years):
                r[t, :] = np.exp(alpha_r) * (1 + r[t-1, :])**rho_r \
                    * np.exp(sig_eps_r**2/2) - 1
                ratio[t, :] = alpha_ratio + rho_ratio * ratio[t-1, :]
        else:
            cov = sig_eps_r * sig_eps_ratio * self.corr_housing_price_rent
            m_cov = np.array([[sig_eps_r**2, cov],
                              [cov, sig_eps_ratio**2]])
            eps = np.random.multivariate_normal(
                [0, 0], m_cov, size=(common.future_years, common.nsim))
            eps_r, eps_ratio = eps[:, :, 0], eps[:, :, 1]

            for t in range(1, common.future_years):
                r[t, :] = np.exp(alpha_r) * (1+r[t-1, :])**rho_r \
                    * np.exp(eps_r[t, :]) - 1
                ratio[t, :] = alpha_ratio + rho_ratio * ratio[t-1, :] \
                    + eps_ratio[t, :]
        return (1+r) * (1 + self.inflation_rate) - 1, ratio

    def prepare_inflation_factors(self, common):
        """
        Compute inflation factors with base year 2018.

        Parameters
        ----------
        common: Common
            instance of the class Common

        Returns
        -------
        dict:
            Dictionary of inflation factors for each year
        """
        start_year = common.base_year - common.past_years
        end_year = common.base_year + common.future_years
        # future inflation
        d_infl_factors = {
            year: (1 + self.inflation_rate)**(year-common.base_year)
            for year in range(common.base_year, end_year)}
        # past inflation
        d_inflation = tools.get_params(
            module_dir + path_params + 'inflation.csv', numerical_key=True)
        for year in reversed(range(start_year, common.base_year)):
            d_infl_factors[year] = (d_infl_factors[year + 1]
                                    / (1 + d_inflation[year]))
        return d_infl_factors

    def simulate_interest_debt(self):
        """
        Creates N series of yearly nominal interest rate of length T
        for each type of debt

        Returns
        -------
        dict:
            Dictionary of interest rates by type of debt and year
        """
        mix_fee_debts = pd.read_csv(
            module_dir + path_params + "mix_fee_debt.csv",
            usecols=list(range(5)), index_col=0).to_dict('index')
        # monthly rates:
        d_interest = {}
        for debt in mix_fee_debts:
            d_interest[debt] = (mix_fee_debts[debt]['bills']*self.ret_bills
                                + mix_fee_debts[debt]['bonds']*self.ret_bonds
                                + mix_fee_debts[debt]['fee'])
            d_interest[debt][0] = mix_fee_debts[debt]['value_2018']

        return d_interest

    def attach_diff_log_wages(self):
        """
        Creates a dictionary of differences in log wages by education and age.

        Returns
        -------
        dict:
            Dictionary of difference in log wages by education and age
        """
        diff_log_wages = pd.read_csv(
            module_dir + path_params + 'diff_log_wage.csv', index_col=0)
        d_diff_log_wages = {}
        for degree in diff_log_wages.columns:
            d_diff_log_wages[degree] = np.cumsum(
                diff_log_wages[degree].values + np.log(1 + self.gr_rate_wage))
        return d_diff_log_wages

    def initialize_factors(self):
        """
        This function creates an instance of life.table
        by gender and province.

        Returns
        -------
        dict:
            dictionary of annuity factors by gender and provinces
        """
        l_sex = ['male', 'female']
        l_prov = ['qc', 'on', 'ab', 'bc', 'sk', 'ns', 'nb', 'mb', 'pe', 'nl']
        d_factors = {}
        for s in l_sex:
            d_factors[s] = {}
            for p in l_prov:
                d_factors[s][p] = life.table(prov=p, scenario='M',
                                             gender=s+'s')
        with open(module_dir + path_factors + 'd_factors.pickle', 'wb') as file:
            pickle.dump(d_factors, file)
        return d_factors
