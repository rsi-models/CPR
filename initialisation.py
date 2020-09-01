import importlib
import numpy as np
from CPR import assets
from CPR import debts
importlib.reload(assets)
importlib.reload(debts)


def create_hh(index, d_hh, common, prices):
    """
    Create a household with all the data attached to it.
    """

    # initialize household and spouses:
    l_hh = ['prov', 'couple', 'mix_bills', 'mix_bonds', 'mix_equity', 'fee',
            'fee_equity']
    l_sp = ['byear', 'sex', 'education', 'ret_age', 'claim_age_cpp',
            'init_wage', 'pension', 'init_room_rrsp', 'init_room_tfsa',
            'bal_rrsp', 'bal_tfsa', 'bal_other_reg', 'bal_unreg',
            'cap_gains_unreg', 'realized_losses_unreg',
            'cont_rate_rrsp', 'cont_rate_tfsa', 'cont_rate_other_reg',
            'cont_rate_unreg', 'withdrawal_rrsp', 'withdrawal_tfsa',
            'withdrawal_other_reg', 'withdrawal_unreg',
            'replacement_rate_db', 'rate_employee_db', 'income_previous_db',
            'init_dc', 'rate_employee_dc', 'rate_employer_dc']

    # create households with 1 or 2 people
    p = Person(d_hh, l_sp, common, prices)  # first p
    if not d_hh['couple']:
        hh = Hhold(d_hh, l_hh, index, common, p)
    else:  # sp0 is first to retire
        l_s_p = ['s_' + var for var in l_sp]
        s_p = Person(d_hh, l_s_p, common, prices, s_=True)
        if p.ret_year <= s_p.ret_year:
            hh = Hhold(d_hh, l_hh, index, common, p, s_p)
        else:
            hh = Hhold(d_hh, l_hh, index, common, s_p, p)

    # initialize financial assets and rpp_dc:
    for p in hh.sp:
        p.fin_assets = {}
        if np.isnan(p.bal_tfsa):  # create tfsa account
            p.bal_tfsa, p.cont_rate_tfsa, p.withdrawal_tfsa = 0, 0, 0
        if np.isnan(p.bal_unreg):  # create unreg account
            p.bal_unreg, p.cont_rate_unreg, p.withdrawal_unreg = 0, 0, 0
            p.cap_gains_unreg, p.realized_losses_unreg = 0, 0

        p.fin_assets['unreg'] = assets.UnregAsset(p, hh, prices)
        for acc in ['rrsp', 'tfsa', 'other_reg']:
            if getattr(p, f'bal_{acc}') >= 0:
                p.fin_assets[acc] = assets.FinAsset(p, hh, acc)

    # initialize rpp_dc:
        if p.init_dc >= 0:
            p.rpp_dc = assets.RppDC(p, common)

    # initialize rpp_db:
        if (p.replacement_rate_db > 0) | (p.income_previous_db > 0):
            p.rpp_db = assets.RppDB(p)

    # initialize residences and business
    hh.residences = {}
    for resid in ['first_residence', 'second_residence']:
        if d_hh[resid] > 0:
            hh.residences[resid] = assets.RealAsset(d_hh, resid)
    if d_hh['business'] > 0:
        hh.business = assets.Business(d_hh)

    # initialize debts:
    hh.debts = {}
    l_debts = ['credit_card', 'personal_loan', 'student_loan', 'car_loan',
               'credit_line', 'first_mortgage', 'second_mortgage',
               'other_debt']
    for debt in l_debts:
        if d_hh[debt] > 0:
            hh.debts[debt] = debts.Debt(debt, d_hh, common, prices)
    return hh


class Person:
    """
    This class creates a person.
    """
    def __init__(self, d_hh, l_sp, common, prices, s_=False):
        if s_:  # removes 's_' in front of variable names
            d_sp = {k[2:]: v for k, v in d_hh.items() if k in l_sp}
            self.who = 's_'  # to compare input and output data
        else:
            d_sp = {k: v for k, v in d_hh.items() if k in l_sp}
            self.who = ''
        self.__dict__.update(d_sp)
        self.byear = int(self.byear)  # s_byear is float because NaNs in column
        self.age = self.init_age = common.base_year - self.byear
        self.contribution_room = assets.ContributionRoom(self.init_room_rrsp,
                                                         self.init_room_tfsa)
        self.ret_age = min(int(self.ret_age), common.max_ret_age)
        self.ret_year = self.byear + self.ret_age
        self.retired = False
        # initialize cpp_qpp
        self.cpp = 0
        self.claim_age_cpp = np.clip(self.ret_age, common.min_claim_age_cpp,
                                     common.max_claim_age_cpp)
        for acc in ['rrsp', 'rpp_dc', 'tfsa', 'tfsa_0', 'unreg', 'unreg_0',
                    'return']:
            setattr(self, f'annuity_{acc}_real', 0)
        # create wage_profile
        self.wage_profile = self.create_wage_profile(common, prices)

    def create_wage_profile(self, common, prices):
        """
        Create wage profiles for each realisation of uncertainty.

        Parameters
        ----------
        common: Common
            instance of the class Common
        prices: Prices
            instance of the class Prices

        Returns
        -------
        np.array:
            wage profiles
        """
        rel_age = self.age - common.min_age_cpp
        rel_ret_age = self.ret_age - common.min_age_cpp
        rel_max_age = common.future_years - common.min_age_cpp

        log_wages = np.zeros(rel_max_age)
        diffs = prices.d_diff_log_wages[self.education]
        diffs = diffs[:rel_ret_age] - diffs[rel_age]
        log_wages[:rel_ret_age] = (np.log(self.init_wage) + diffs)
        log_wages = np.repeat(log_wages.reshape(-1, 1), common.nsim, axis=1)

        if common.non_stochastic is False:
            log_wages[rel_age+1:rel_ret_age, :] += \
                self.create_shocks(rel_ret_age-rel_age-1, common.nsim, prices)
            log_wages[:rel_age, :] += \
                np.flipud(self.create_shocks(rel_age, common.nsim, prices))

        return np.where(log_wages > 1, np.exp(log_wages), 0)

    def create_shocks(self, T, N, prices):
        """
        Create time series on shocks to the wage.

        Parameters
        ----------
        T: int
            length of the time series
        N: int
            number of realisations
        prices: Prices
            instance of the class Prices

        Returns
        -------
        np.array:
            time series on shocks to the wage
        """
        if T == 0:
            return np.zeros((1, N))
        eps_trans = np.random.normal(0, prices.sig_trans_wage, (T, N))
        eps_pers = np.random.normal(0, prices.sig_pers_wage, (T, N))
        shock_pers = np.zeros((T, N))
        shock_pers[0, :] = eps_pers[0, :]
        for t in range(1, T):
            shock_pers[t, :] = prices.rho_wage * shock_pers[t-1, :] \
                + eps_pers[t, :]
        return eps_trans + shock_pers


class Hhold():
    """
    This class creates a household.
    """
    def __init__(self, d_hh, l_hhold, index, common, p0, p1=None):
        self.sp = [p0] if p1 is None else [p0, p1]
        d_hhold = {k: v for k, v in d_hh.items() if k in l_hhold}
        self.__dict__.update(d_hhold)
        self.index = index
        self.set_other_years(common)

    def set_other_years(self, common):
        """
        Set years of partial and full retirement as well as
        years in which pre-retirement and post-retirement consumptions
        are assessed.

        Parameters
        ----------
        common: Common
            instance of the class Common
        """
        # consumption before retirement at age_cons_bef_ret but after 2018
        # and before first retirement
        self.cons_bef_ret_year = np.clip(
            self.sp[0].byear + common.age_cons_bef_ret,
            common.base_year, self.sp[0].ret_year - 1)

        if self.couple is False:
            self.ret_year = self.sp[0].ret_year
            self.cons_after_ret_year = max(
                self.sp[0].byear + common.official_ret_age, self.ret_year)
        else:
            self.ret_year = self.sp[1].ret_year  # p[1] is last to retire
            if self.sp[0].ret_year < self.sp[1].ret_year:
                self.partial_ret_year = self.sp[0].ret_year
            self.cons_after_ret_year = max(
                self.sp[1].byear + common.official_ret_age, self.ret_year)
