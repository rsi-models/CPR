import heapq
import numpy as np
from CPR import tools


class ContributionRoom:
    """
    This class manages contribution room for TFSAs and RRSPs.

    All amounts are nominal.

    Parameters
    ----------
    init_room_rrsp: float
        initial RRSP contribution room available
    init_room_tfsa: float
        initial TFSA contribution room available
    """
    def __init__(self, init_room_rrsp, init_room_tfsa):
        self.init_room_rrsp = init_room_rrsp
        self.init_room_tfsa = init_room_tfsa
        self.reset()

    def compute_contributions(self, p, year, common, prices):
        """
        Function to update contribution room for RRSPs and TFSAs, using the 2 other functions below (which themselves call the other functions of the class).

        Parameters
        ----------
        p: Person
            instance of the class Person
        year : int
            year
        common : Common
            instance of the class Common
        prices : Prices
            instance of the class Prices
        """
        self.update_rrsp_room(p, year, common)
        self.update_tfsa_room(p, year, common)
        self.extra_contrib_rrsp = 0
        if (p.replacement_rate_db > 0) & (year < common.base_year
                                          + common.max_years_db):
            self.adjust_db_contributions(p, year, common)
        if hasattr(p, 'rpp_dc'):
            self.adjust_dc_contributions(p, year)
        for acc in set(p.fin_assets) & set(('rrsp', 'other_reg')):
            self.adjust_rrsp_contributions(acc, p, year)

        self.adjust_tfsa_contributions(p, year, common, prices)

        self.adjust_unreg_contributions(p, year)

    def update_rrsp_room(self, p, year, common):
        """
        Function to update RRSP contribution room.

        Parameters
        ----------
        p: Person
            instance of the class Person
        year : int
            year
        common : Common
            instance of the class Common
        """
        if p.age > common.max_age_no_rrif:
            self.room_rrsp = 0
        else:
            self.room_rrsp += min(common.perc_rrsp * p.d_wages[year-1],
                                  common.d_rrsp_limit[year])

    def update_tfsa_room(self, p, year, common):
        """
        Function to update TFSA contribution room.

        Parameters
        ----------
        p: Person
            instance of the class Person
        year : int
            year
        common : Common
            instance of the class Common
        """
        self.room_tfsa += common.d_tfsa_limit[year]
        self.room_tfsa += p.fin_assets['tfsa'].withdrawal

    def adjust_db_contributions(self, p, year, common):
        """
        Function to adjust RRSP contribution room to DB RPP contributions.

        Parameters
        ----------
        p: Person
            instance of the class Person
        year : int
            year
        common : Common
            instance of the class Common
        """
        cpp_offset = (common.perc_cpp_2018
                      * min(p.d_wages[year-1], common.d_ympe[year-1])
                      / common.max_years_db)
        benefits_earned = (p.replacement_rate_db * p.d_wages[year-1]
                           / common.max_years_db - cpp_offset)
        pension_credit = max(0, common.db_benefit_multiplier * benefits_earned
                             - common.db_offset)
        self.room_rrsp -= min(pension_credit, self.room_rrsp)

    def adjust_dc_contributions(self, p, year):
        """
        Function to adjust RRSP contribution room to DC RPP contributions.

        If contribution room is insufficent for the intended/planned RRSP contributions, the "excess" contributions are channeled to TFSA.

        Parameters
        ----------
        p: Person
            instance of the class Person
        year : int
            year
        """
        contrib = p.rpp_dc.contrib_rate * p.d_wages[year]
        if contrib <= self.room_rrsp:
            p.rpp_dc.contribution = contrib
            self.room_rrsp -= contrib
        else:
            p.rpp_dc.contribution = self.room_rrsp
            self.extra_contrib_rrsp += contrib - self.room_rrsp
            self.room_rrsp = 0
        self.adjust_employees_contributions(p)

    def adjust_employees_contributions(self, p):
        """
        Function to compute employee contributions to DC RPPs (later used to caculate taxes).

        Parameters
        ----------
        p: Person
            instance of the class Person
        """
        if p.rpp_dc.contrib_rate == 0:
            p.contrib_employee_dc = 0
        else:
            p.contrib_employee_dc = (p.rate_employee_dc /
                                     p.rpp_dc.contrib_rate
                                     * p.rpp_dc.contribution)

    def adjust_rrsp_contributions(self, acc, p, year):
        """
        Function to adjust RRSP contribution for contributions other than to RPPs.

        If contribution room is insufficent for the intended/planned RRSP contributions, the "excess" contributions are channeled to TFSA.

        Parameters
        ----------
        acc : [type]
            [description]
        p: Person
            instance of the class Person
        year : int
            year
        """
        contrib = p.fin_assets[acc].contrib_rate * p.d_wages[year]
        if contrib <= self.room_rrsp:
            p.fin_assets[acc].contribution = contrib
            self.room_rrsp -= contrib
        else:
            p.fin_assets[acc].contribution = self.room_rrsp
            self.extra_contrib_rrsp += contrib - self.room_rrsp
            self.room_rrsp = 0

    def adjust_tfsa_contributions(self, p, year, common, prices):
        """
        Function to adjust TFSA contribution room to TFSA contributions (including "excess" DC RPP and RRSP contributions).

        If contribution room is insufficent for the intended/planned TFSA contributions, the "excess" contributions are channeled to unregistered accounts.

        Parameters
        ----------
        p: Person
            instance of the class Person
        year : int
            year
        common : Common
            instance of the class Common
        prices : Prices
            instance of the class Prices
        """
        self.extra_contrib_tfsa = 0
        contrib = p.fin_assets['tfsa'].contrib_rate * p.d_wages[year]
        contrib += self.extra_contrib_rrsp
        if p.age > common.max_age_no_rrif:
            contrib += self.adjust_rrif(p, year, common, prices)

        if contrib <= self.room_tfsa:
            p.fin_assets['tfsa'].contribution = contrib
            self.room_tfsa -= contrib
        else:
            p.fin_assets['tfsa'].contribution = self.room_tfsa
            self.extra_contrib_tfsa += contrib - self.room_tfsa
            self.room_tfsa = 0

    def adjust_rrif(self, p, year, common, prices):
        """
        Function to adjust DC RPP and RRSP accounts to mandatory withdrawals.

        Parameters
        ----------
        p: Person
            instance of the class Person
        year : int
            year
        common : Common
            instance of the class Common
        prices : Prices
            instance of the class Prices

        Returns
        -------
        [type]
            [description]
        """
        rrif_transfer_real = 0
        for acc in set(p.fin_assets) & set(('rpp_dc', 'rrsp', 'other_reg')):
            rrif_transfer_real += p.fin_assets[acc].rrif_withdrawal(p, common)
        return rrif_transfer_real * prices.d_infl_factors[year]

    def adjust_unreg_contributions(self, p, year):
        """
        Function to adjust contributions to unregistered accounts for "excess" TFSA contributions channeled to them.

        Parameters
        ----------
        p: Person
            instance of the class Person
        year : int
            year
        """
        contrib = p.fin_assets['unreg'].contrib_rate * p.d_wages[year]
        contrib += self.extra_contrib_tfsa
        p.fin_assets['unreg'].contribution = contrib

    def reset(self):
        """
        Reset RRSP and TFSA contribution rooms to their inital values.
        """
        self.room_rrsp = self.init_room_rrsp
        self.room_tfsa = self.init_room_tfsa


class FinAsset:
    """
    This class manages registered accounts. All amounts are nominal.

    Parameters
    ----------
    p: Person
        spouse
    hh: Hhold
        household
    """
    def __init__(self, p, hh, acc):
        self.init_balance = getattr(p, f'bal_{acc}')
        self.contrib_rate = getattr(p, f'cont_rate_{acc}')
        self.init_desired_withdrawal_real = getattr(p, f'withdrawal_{acc}')
        self.mix_bills = hh.mix_bills
        self.mix_bonds = hh.mix_bonds
        self.mix_equity = hh.mix_equity
        self.fee = hh.fee
        self.reset()

    def update(self, d_returns, year, common, prices):
        """
        Function to update the balance to account for contributions, withdrawals, and returns.

        Parameters
        ----------
        d_returns : dict
            dictionary of returns
        year : int
            year
        common : Common
            instance of the class Common
        prices : Prices
            instance of the class Prices
        """
        self.nom, self.real = tools.create_nom_real(year, prices)
        self.balance *= 1 + self.rate(d_returns, year)
        self.balance += self.contribution
        self.desired_withdrawal = self.nom(self.desired_withdrawal_real)
        self.withdrawal = min(self.balance, self.desired_withdrawal)
        self.balance -= self.withdrawal

    def rate(self, d_returns, year):
        """
        Function to compute the rate of return given the mix of assets in the account.

        Parameters
        ----------
        d_returns : dict
            dictionary of returns
        year : int
            year

        Returns
        -------
        float
            
            Rate of return (net of fees).
        """
        return (self.mix_bills*d_returns['bills'][year]
                + self.mix_bonds*d_returns['bonds'][year]
                + self.mix_equity*d_returns['equity'][year] - self.fee)

    def rrif_withdrawal(self, p, common):
        """
        Function to manage mandatory RRIF withdrawals.

        Parameters
        ----------
        p: Person
            instance of the class Person
        common : Common
            instance of the class Common

        Returns
        -------
        float
            Amount of mandatory withdrawal.
        """
        if self.balance > 0:
            extra_withdrawal_real = max(
                0, common.d_perc_rrif[p.age] * self.real(self.balance)
                - self.desired_withdrawal_real)
            self.desired_withdrawal_real += extra_withdrawal_real
        else:
            extra_withdrawal_real = 0

        return extra_withdrawal_real

    def liquidate(self):
        """
        Function to liquidate an account, setting balance, contributions and withdrawals to zero.
        
        Returns
        -------
        float
            Amount from liquidation (before taxes).
        """
        value = self.balance
        self.balance, self.contribution = 0, 0
        return value

    def reset(self):
        """
        Reset the balance and withdrawal to its initial balance.
        """
        self.balance = self.init_balance
        self.desired_withdrawal_real = self.init_desired_withdrawal_real
        self.withdrawal = 0  # to adjust contribution space tfsa first period


class UnregAsset:
    """
    This class manages unregistered accounts.

    All amounts are nominal.

    Parameters
    ----------
    p: Person
        spouse
    hh: Hhold
        household
    prices: Prices
        instance of the class Prices
    """
    def __init__(self, p, hh, prices):
        self.init_balance = p.bal_unreg
        self.contrib_rate = p.cont_rate_unreg
        self.desired_withdrawal = p.withdrawal_unreg
        self.init_cap_gains = p.cap_gains_unreg
        self.init_realized_losses = p.realized_losses_unreg
        self.mix_bills = hh.mix_bills
        self.mix_bonds = hh.mix_bonds
        self.mix_equity = hh.mix_equity
        self.fee = hh.fee
        self.fee_equity = hh.fee_equity
        self.ret_dividends = prices.ret_dividends
        self.reset()

    def update(self, d_returns, year, common, prices):
        """
        Function to update the balance for contributions, withdrawals and returns.

        Parameters
        ----------
        d_returns : dict
            dictionary of returns
        year : int
            year
        common : Common
            instance of the class Common
        prices : Prices
            instance of the class Prices
        """
        self.nom = tools.create_nom(year, prices)
        self.compute_income(d_returns, year)
        self.update_balance()
        self.prepare_withdrawal()
        self.adjust_income()
        self.withdrawal_cap_losses = self.adjust_cap_losses(
            self.withdrawal_cap_gains)
        self.adjust_final_balance()
        self.amount_after_tax = 0
        self.income_to_tax = bool(self.inc_div + self.inc_int)

    def compute_income(self, d_returns, year):
        """
        Function to compute new capital gains and taxable income (dividends and interests).

        Parameters
        ----------
        d_returns : dict
            dictionary of returns
        year : int
            year
        """
        # to simplify, we assume constant dividend rate and fees paid out
        # of capital gains.
        self.inc_div = self.balance * self.mix_equity * self.ret_dividends
        self.inc_cap_gains = (
            self.balance * self.mix_equity
            * (d_returns['equity'][year] - self.fee_equity)
            - self.inc_div)
        self.inc_int = (self.balance * self.rate(d_returns, year)
                        - self.inc_div - self.inc_cap_gains)

    def rate(self, d_returns, year):
        """
        Function that computes the rate of return given the mix of assets in account.

            dictionary of returns
        year : int
            year

        Returns
        -------
        float
            Rate of return (net of fees).
        """
        return (self.mix_bills*d_returns['bills'][year] +
                self.mix_bonds*d_returns['bonds'][year] +
                self.mix_equity*d_returns['equity'][year] - self.fee)

    def update_balance(self):
        """
        Function to update to balance and separate between non-taxable funds (i.e. previous post-tax balance), capital gains, dividends, and interests.
        """
        self.non_taxable += self.amount_after_tax
        self.non_taxable += self.contribution
        self.cap_gains += self.inc_cap_gains
        self.balance = (self.non_taxable + self.cap_gains + self.inc_int
                        + self.inc_div)

    def prepare_withdrawal(self):
        """
        Function to separate a withdrawal from the balance at the end of the period, and separately identify non-taxable funds, capital gains, dividends, and interests.
        """
        self.withdrawal = min(self.nom(self.desired_withdrawal), self.balance)
        self.share_withdrawal = self.withdrawal / (self.balance + 1e-12)
        self.withdrawal_non_tax = self.share_withdrawal * self.non_taxable
        self.withdrawal_cap_gains = self.share_withdrawal * self.cap_gains
        self.withdrawal_div = self.share_withdrawal * self.inc_div
        self.withdrawal_int = self.share_withdrawal * self.inc_int

    def adjust_income(self):
        """
        Function to adjust investment income (dividends and interests) for withdrawals.
        """
        self.inc_div *= 1 - self.share_withdrawal
        self.inc_int *= 1 - self.share_withdrawal

    def adjust_cap_losses(self, realized_cap_gains):
        """
        Function to compute capital losses from previous years used for deduction against capital gains, and adjust realized capital losses accordingly.

        Parameters
        ----------
        realized_cap_gains : float
            capital gains

        Returns
        -------
        float
            Capital losses (to be deducted).
        """
        if realized_cap_gains > 0:
            used_cap_losses = min(realized_cap_gains, self.realized_losses)
            self.realized_losses = used_cap_losses
        else:
            self.realized_losses += -realized_cap_gains
            used_cap_losses = 0

        return used_cap_losses

    def adjust_final_balance(self):
        """
        Function that adjusts the final balance for withdrawals, dividends and interests.
        """
        self.non_taxable *= (1 - self.share_withdrawal)
        self.cap_gains *= (1 - self.share_withdrawal)
        self.balance = int(self.non_taxable + self.cap_gains)
        # int to avoid approx errors

    def liquidate(self):
        """
        Function to liquidate the account and adjust capital losses.
        """
        self.liquidation_non_taxable = self.non_taxable
        self.liquidation_cap_gains = self.cap_gains
        self.balance, self.non_taxable, self.cap_gains = 0, 0, 0
        self.inc_int, self.inc_div = 0, 0

        self.liquidation_cap_losses = self.adjust_cap_losses(
            self.liquidation_cap_gains)

    def reset(self):
        """
        Function to reset the balance, capital gains, and withdrawals to their initial values.
        """
        self.balance = self.init_balance
        self.cap_gains = self.init_cap_gains
        self.non_taxable = self.balance - self.cap_gains
        self.realized_losses = self.init_realized_losses
        self.amount_after_tax = 0
        self.liquidation_non_taxable = 0
        self.liquidation_cap_gains = 0
        self.liquidation_cap_losses = 0


class RppDC(FinAsset):
    """
    This class manages DC RPPs.

    All amounts are nominal.

    Parameters
    ----------
    p: Person
        spouse
    common: Common
        instance of the class Common
    """
    def __init__(self, p, common):
        self.init_balance = p.init_dc
        self.contrib_rate = p.rate_employee_dc + p.rate_employer_dc
        self.init_desired_withdrawal_real = 0
        self.mix_bills = common.mix_bills_rpp
        self.mix_bonds = common.mix_bonds_rpp
        self.mix_equity = common.mix_equity_rpp
        self.fee = common.fee_rpp
        self.reset()


class RppDB:
    """
    This class manages DB RPPs.

    All amounts are nominal.

    Parameters
    ----------
    p: Person
        spouse
    """
    def __init__(self, p):
        self.init_rate_employee_db = p.rate_employee_db
        self.replacement_rate_db = p.replacement_rate_db
        self.income_previous_db = p.income_previous_db
        self.reset()

    def compute_benefits(self, p, common):
        """
        Function that computes RPP DB benefits and adjusts them for CPP/QPP integration.

        If RPP benefits are smaller than CPP/QPP benefits, RPP benefits are set to zero once the receipt of CPP/QPP retirement benefits begins.

        Parameters
        ----------
        p: Person
            instance of the class Person
        common : Common
            instance of the class Common
        """
        if self.replacement_rate_db > 0:
            n = common.n_best_wages_db
            l_wages = [wage for wage in p.d_wages.values()]
            n_highest_wages = sorted(l_wages, reverse=True)[:n]
            self.mean_best_wage = sum(n_highest_wages) / n

            self.adjust_for_penalty(p, common)

            if p.age >= common.official_ret_age:
                self.benefits -= min(self.compute_cpp_adjustment(p, common),
                                     self.benefits_current_empl)

        if self.income_previous_db > 0:
            self.benefits += self.income_previous_db

    def adjust_for_penalty(self, p, common):
        """
        Function to compute a penalty for individuals who begin to receive DB RPP benefits "early", i.e. before they accumulate the maximum number of years of service, if they are younger than the age at which benefits can start without penalty (the "early retirement age").

        By default, the penalty applies to those who begin RPP benefits receipt before reaching 35 years of service and before age 62. These values can be modified.

        Parameters
        ----------
        p: Person
            instance of the class Person
        common : Common
            instance of the class Common
        """
        years_service = p.replacement_rate_db / common.perc_year_db
        cond0 = years_service < common.max_years_db
        cond1 = p.ret_age < common.db_ret_age_no_penalty
        if cond0 and cond1:
            years_early_db = common.official_ret_age - p.ret_age
        else:
            years_early_db = 0

        self.benefits_current_empl = (
            self.replacement_rate_db * self.mean_best_wage
            * (1 - years_early_db * common.db_penalty_early_ret))
        self.benefits += self.benefits_current_empl

    def compute_cpp_adjustment(self, p, common):
        """
        Function to compute an adjustment (reduction) to DB RPP benefits to account for CPP/QPP integration.

        Start in base year if enough years until retirement, otherwise go
        backward from year before retirement.

        Parameters
        ----------
        p: Person
            instance of the class Person
        common : Common
            instance of the class Common

        Returns
        -------
        float
            Amount of benefit adjustment for CPP/QPP integration.
        """
        years_db = int(self.replacement_rate_db / common.perc_year_db)

        if years_db <= p.ret_year - common.base_year:
            mean_wage = np.mean([min(p.d_wages[common.base_year + t],
                                     common.d_ympe[common.base_year + t])
                                 for t in range(years_db)])
        else:
            mean_wage = np.mean([min(p.d_wages[p.ret_year - t],
                                     common.d_ympe[p.ret_year - t])
                                 for t in range(1, years_db + 1)])

        return (common.perc_cpp_2018 * years_db / common.max_years_db
                * mean_wage)

    def reset(self):
        """
        Function that resets the benefits, catpial gains and withdrawal to their initial values.
        """
        self.benefits = 0
        self.rate_employee_db = self.init_rate_employee_db


class RealAsset:
    """
    This class manages housing and residences.

    All amounts are nominal.

    Parameters
    ----------
    d_hh: dict of float
        dictionnary containing values of residences
    resid: str
        primary or secondary residence
    """
    def __init__(self, d_hh, resid):
        self.init_balance = d_hh[resid]
        self.price = d_hh[f'price_{resid}']
        self.reset()

    def update(self, growth_rates, year, prices):
        """
        Function to update the balance (residence values) for growth in price.

        Parameters
        ----------
        growth_rates : dict
            nominal return to housing (capital gains)
        year : int
            year
        prices : Prices
            instance of the class Prices
        """
        self.balance *= 1 + growth_rates[year]

    def liquidate(self):
        """
        Function to liquidate the asset, compute capital gains if they apply, and set balance to zero.

        Returns
        -------
        float
            Amount from asset liquidation (before taxes).
        """
        self.liquidation_non_taxable = self.price
        self.liquidation_cap_gains = self.balance - self.price
        self.balance = 0

    def reset(self):
        """
        Function to reset balance to its initial value and set capital gains to zero.
        """
        self.balance = self.init_balance
        self.cap_gains = 0

    def impute_rent(self, hh, year, prices):
        """
        Function to compute imputed rent.

        Parameters
        ----------
        hh: Hhold
            household
        year : int
            year
        prices : Prices
            instance of the class Prices
        """
        hh.imputed_rent = (hh.residences['first_residence'].balance
                           / prices.d_price_rent_ratio[year])


class Business:
    """
    This class manages a business (as an asset owned by the houshehold).

    All amounts are nominal.

    Parameters
    ----------
    hh: Hhold
        household
    """
    def __init__(self, d_hh):
        self.init_balance = d_hh['business']
        self.price = d_hh['price_business']
        self.reset()

    def update(self, d_business_returns, year, prices):
        """
        Function to update the balance and dividends.

        Parameters
        ----------
        d_business_returns : dict
            returns on business assets
        year : int
            year
        prices : Prices
            instance of the class Prices
        """
        self.dividends_business = self.balance * prices.ret_dividends
        self.balance *= 1 + d_business_returns[year] - prices.ret_dividends

    def liquidate(self, common):
        """
        Function to liquidate account (business assets), compute capital gains, and set balance to zero.

        Parameters
        ----------
        common : Common
            instance of the class Common

        Returns
        -------
        float
            Selling price of the business assets.
        """
        self.liquidation_non_taxable = self.price
        self.liquidation_cap_gains = self.balance - self.price
        self.balance = 0

    def reset(self):
        """
        Reset business value and capital gains to their initial values.
        """
        self.balance = self.init_balance
        self.cap_gains = self.init_balance - self.price
