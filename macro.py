import importlib
import pandas as pd
import numpy as np
import pickle
from life import life
import srpp
import srd
import tools
importlib.reload(tools)


class CommonParameters:
    """
    Class setting and containing the parameters common to all households.
    """
    def __init__(self, nsim, non_stochastic, extra_params):

        self.nsim = nsim
        self.non_stochastic = non_stochastic
        for file in ['common_params.csv', 'user_options.csv']:
            tools.add_params_as_attr(self, '../data/pars/' + file)
        tools.change_params(self, extra_params)

        self.prepare_srd(self.year_srd)

        self.rules_cpp = srpp.rules()
        self.rules_qpp = srpp.rules(qpp=True)  

        for args in [('rrsp_limit', 2021), ('tfsa_limit', 2019)]:
            self.prepare_limits(*args)
        self.d_ympe = self.prepare_ympe()

        self.d_perc_cpp = {year: getattr(self, f'perc_cpp_{year}')
                           for year in range(2018, 2023)}
        self.d_perc_cpp.update(
            {year: self.perc_cpp_2023
             for year in range(2023, self.base_year + self.future_years)})
        self.d_perc_rrif = tools.get_params(
            '../data/pars/rrif_rates.csv', numerical_key=True)

    def prepare_srd(self, year):
        """
        Initialize SRD

        Parameters
        ----------`
        year: int
            year
        """
        self.tax = srd.tax(year=year)

        return rules, rules.ympe(self.base_year)

    def prepare_limits(self, name, last_year_data):
        d = {}
        for year in range(self.base_year, self.base_year + self.future_years):
            if year <= last_year_data:
                d[year] = getattr(self, f'{name}_{year}')
            else:
                d[year] = round(d[year-1] * (1+getattr(self, f'gr_{name}')))
        setattr(self, f'd_{name}', d)
    
    def prepare_ympe(self):
        """"
        Pre-reform ympe used to adjust DB benefits for CPP
        """
        d_ympe = tools.get_params('../data/pars/ympe.csv',
                                       numerical_key=True)
        for year in range(max(d_ympe.keys()) + 1,
                          self.base_year + self.future_years):
            d_ympe[year] = round(d_ympe[year-1] * (1 + self.gr_ympe))
        return d_ympe
            



class Prices:
    """
    This class set the assumptions on macroeconomics, return on assets
    and the cost of debt.

    1. Load parameters value from the ../data/pars/prices.csv file.
    2. Simulates a time series of stochastic bill returns for each simulations.
    3. Simulates a time series of stochastic bond returns for each simulations.
    4. Simulates a time series of stochastic equity returns
    for each simulation.
    5. Simulates a time series of stochastic housing returns
    for each simulation.
    6. Simulates a time series of stochastic business returns
    for each simulation.
    7. Simulates a time series of stochastic interest rates on debts
    for each simulation.
    8. Load wage profiles.
    9. Create instance of the life.table module if necessary.
    """
    def __init__(self, common, extra_params):
        tools.add_params_as_attr(self, '../data/pars/prices.csv')
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
            with open('../data/precomputed/d_factors', 'rb') as file:
                self.d_factors = pickle.load(file)

    def simulate_ret(self, asset, common):
        """
        Simulate N series of length T nominal returns distributed lognormally
        with autocorrelation rho.  
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

    def simulate_housing(self, common):
        """
        Simulate series of nominal housing price growth (in log(1+r) form)
        and price-rent ratio.  
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
            eps_r, eps_ratio = eps[:, : , 0], eps[:, : , 1]

            for t in range(1, common.future_years):
                r[t, :] = np.exp(alpha_r) * (1+r[t-1, :])**rho_r \
                    * np.exp(eps_r[t, :]) - 1
                ratio[t, :] = alpha_ratio + rho_ratio * ratio[t-1, :] \
                    + eps_ratio[t, :] 
        return (1+r) * (1 + self.inflation_rate) - 1, ratio

    def compute_params_process(self, mu, rho, sigma):
        """
        Converts arithmetic mean mu, volatility sigma of the returns 
        and autocorrelation rho of the log returns into 
        alpha, rho and sig_eps of the process 
        $$ \ln(1+r_t) = \alpha + \rho * ln(1+r{t-1}) + \epsilon $$,
        where $$ \epsilon \tilde N(0, sig_eps).
        """
        m, v = (1+mu), sigma**2
        sig_lognorm = np.sqrt(np.log(1 + v / m**2))
        mu_lognorm = np.log(m / np.sqrt(1 + v / m**2))
        alpha = (1-rho) * mu_lognorm
        sig_eps = np.sqrt(1 - rho**2) * sig_lognorm
        return alpha, sig_eps

    def prepare_inflation_factors(self, common):
        start_year = common.base_year - common.past_years
        end_year = common.base_year + common.future_years
        # future inflation
        d_infl_factors = {
            year: (1 + self.inflation_rate)**(year-common.base_year)
            for year in range(common.base_year, end_year)}
        # past inflation
        d_inflation = tools.get_params('../data/pars/inflation.csv',
                                       numerical_key=True)
        for year in reversed(range(start_year, common.base_year)):
            d_infl_factors[year] = (d_infl_factors[year + 1]
                                    / (1 + d_inflation[year]))
        return d_infl_factors

    def simulate_interest_debt(self):
        """
        Creates N series of yearly interest rate of length T
        for each type of debt

        :rtype: dictionary
        """
        mix_fee_debts = pd.read_csv("../data/pars/mix_fee_debt.csv",
                                    usecols=list(range(5)),
                                    index_col=0).to_dict('index')
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
        Creates a dictionary of differences in log wages by age and education
        """
        diff_log_wages = pd.read_csv('../data/pars/diff_log_wage.csv',
                                     index_col=0)
        d_diff_log_wages = {}
        for degree in diff_log_wages.columns:
            d_diff_log_wages[degree] = np.cumsum(
                diff_log_wages[degree].values + np.log(1 + self.gr_rate_wage))
        return d_diff_log_wages

    def initialize_factors(self):
        """
        This function creates a specific instance of life.table
        by provinces and gender.

        :rtype: dictionary
        """
        l_sex = ['male', 'female']
        l_prov = ['qc', 'on', 'ab', 'bc', 'sk', 'ns', 'nb', 'mb', 'pe', 'nl']
        d_factors = {}
        for s in l_sex:
            d_factors[s] = {}
            for p in l_prov:
                d_factors[s][p] = life.table(prov=p, scenario='M', gender=s+'s')
        with open('../data/precomputed/d_factors', 'wb') as file:
            pickle.dump(d_factors, file)
        return d_factors
