import heapq
import numpy as np
from CPR import tools


class ContributionRoom:
    """
    This class manages contribution rooms for TFSA and RRSP.
    All amounts are nominal.
    
    Parameters
    ----------
    init_room_rrsp: float
        initial room available in rrsp
    init_room_tfsa: float
        initial room available in tfsa
    """
    def __init__(self, init_room_rrsp, init_room_tfsa):
        self.init_room_rrsp = init_room_rrsp
        self.init_room_tfsa = init_room_tfsa
        self.reset()

    def compute_contributions(self, p, year, common, prices):
        """
        Update contribution room for RRSP and TFSA

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
        Update RRSP contribution room.

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
        Update TFSA contribution room.

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
        Adjust contributions room RRSP to DB RPP contribution.

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
        Adjust contribution room RRSP to DC contribution. If insufficent room,
        extra contribution transferred to TFSA.

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
        Compute employee contribution to DC RPP
        (used later to caculate taxes).

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
        Adjust contribution room RRSP for contributions other than RPP.
        If insufficent room, extra contribution transferred to TFSA.

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
        Adjust contribution room TFSA to TFSA contributions
        and excess RRSP contributions. If insufficent room,
        extra contribution transferred to TFSA.

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
        Adjust RPP DC and RRSP to mandatory withdrawals.

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
        Adjust contribution to unregistered accounts
        for excess TFSA contributions.

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
        Reset contribution rooms RRSP and TFSA to inital values.
        """
        self.room_rrsp = self.init_room_rrsp
        self.room_tfsa = self.init_room_tfsa


class FinAsset:
    """
    This class manages registered accounts. All amounts are nominal.
    
    Parameters
    ----------
    p: Person
        spouse in household
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
        Update the balance for contribution, withdrawal and return.

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
        Compute the rate of return given the composition of assets in account.

        Parameters
        ----------
        d_returns : dict
            dictionary of returns
        year : int
            year

        Returns
        -------
        [type]
            [description]
        """
        return (self.mix_bills*d_returns['bills'][year]
                + self.mix_bonds*d_returns['bonds'][year]
                + self.mix_equity*d_returns['equity'][year] - self.fee)

    def rrif_withdrawal(self, p, common):
        """
        Manage mandatory rrif withdrawals.

        Parameters
        ----------
        p: Person
            instance of the class Person
        common : Common
            instance of the class Common

        Returns
        -------
        float
            amount of mandatory withdrawal
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
        Liquidate account, set balance, contribution and withdrawal to zero.

        Returns
        -------
        float
            amount from liquidation (before taxes)
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
    This class manages unregistered account. All amounts are nominal.
    
    Parameters
    ----------
    p: Person
        spouse in household
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
        Update the balance for contribution, withdrawal and return.

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
        Compute new capital gains and taxable income (dividends and interests).

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
        Compute the rate of return given the composition of assets in account.

        Parameters
        ----------
        d_returns : dict
            dictionary of returns
        year : int
            year

        Returns
        -------
        float
            rate of return (net of fee)
        """
        return (self.mix_bills*d_returns['bills'][year] +
                self.mix_bonds*d_returns['bonds'][year] +
                self.mix_equity*d_returns['equity'][year] - self.fee)

    def update_balance(self):
        """
        Update balance and divide between non-taxable, capital gains,
        dividends and interests.
        """
        self.non_taxable += self.amount_after_tax
        self.non_taxable += self.contribution
        self.cap_gains += self.inc_cap_gains
        self.balance = (self.non_taxable + self.cap_gains + self.inc_int
                        + self.inc_div)

    def prepare_withdrawal(self):
        """
        Divide withdrawal from balance at the end of the period
        between non-taxable, capital gains, dividends and interests.
        """
        self.withdrawal = min(self.nom(self.desired_withdrawal), self.balance)
        self.share_withdrawal = self.withdrawal / (self.balance + 1e-12)
        self.withdrawal_non_tax = self.share_withdrawal * self.non_taxable
        self.withdrawal_cap_gains = self.share_withdrawal * self.cap_gains
        self.withdrawal_div = self.share_withdrawal * self.inc_div
        self.withdrawal_int = self.share_withdrawal * self.inc_int

    def adjust_income(self):
        """
        Adjust income for withdrawals.
        """
        self.inc_div *= 1 - self.share_withdrawal
        self.inc_int *= 1 - self.share_withdrawal

    def adjust_cap_losses(self, realized_cap_gains):
        """
        Compute capital losses from previous years used for deduction
        and adjust realized capital losses

        Parameters
        ----------
        realized_cap_gains : float
            capital gains

        Returns
        -------
        float
            capital losses (to be deducted)
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
        Adjust final balance for withdrawal, dividends and interests.
        """
        self.non_taxable *= (1 - self.share_withdrawal)
        self.cap_gains *= (1 - self.share_withdrawal)
        self.balance = int(self.non_taxable + self.cap_gains)
        # int to avoid approx errors

    def liquidate(self):
        """
        Liquidate account and adjust capital losses.
        """
        self.liquidation_non_taxable = self.non_taxable
        self.liquidation_cap_gains = self.cap_gains
        self.balance, self.non_taxable, self.cap_gains = 0, 0, 0
        self.inc_int, self.inc_div = 0, 0

        self.liquidation_cap_losses = self.adjust_cap_losses(
            self.liquidation_cap_gains)

    def reset(self):
        """
        Reset the balance, cap_gains and withdrawal to its initial balance.
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
    This class manages DC RPP. All amounts are nominal.

    Parameters
    ----------
    p: Person
        spouse in household
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
    This class manages DB RPP. All amounts are nominal.
    
    Parameters
    ----------
    p: Person
        spouse in household
    """
    def __init__(self, p):
        self.init_rate_employee_db = p.rate_employee_db
        self.replacement_rate_db = p.replacement_rate_db
        self.income_previous_db = p.income_previous_db
        self.reset()

    def compute_benefits(self, p, common):
        """
        Compute RPP DB benefits and adjust them for CPP.
        If RPP benefits are smaller than CPP benefits,
        RPP benefits are zero when cpp_qpp starts.

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
        DB RPP benefits lowered when less than 35 years of service and
        retirement before age 62.

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
        Compute adjustement to DB RPP for CPP benefits.
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
            amount of CPP adjustment
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
        Reset the benefits, cap_gains and withdrawal to its initial balance.
        """
        self.benefits = 0
        self.rate_employee_db = self.init_rate_employee_db


class RealAsset:
    """
    This class manages housing. All amounts are nominal.
    
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
        Update the balance for growth in price.

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
        Liquidate account, compute capital gains, set balance to zero.

        Returns
        -------
        float
            amount from liquidation (before taxes)
        """
        self.liquidation_non_taxable = self.price
        self.liquidation_cap_gains = self.balance - self.price
        self.balance = 0

    def reset(self):
        """
        Reset balance to its initial balance and set capital gains to zero.
        """
        self.balance = self.init_balance
        self.cap_gains = 0

    def impute_rent(self, hh, year, prices):
        """
        Compute imputed rent.

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
        Update the balance and dividends.

        Parameters
        ----------
        d_business_returns : dict
            business returns
        year : int
            year
        prices : Prices
            instance of the class Prices
        """
        self.dividends_business = self.balance * prices.ret_dividends
        self.balance *= 1 + d_business_returns[year] - prices.ret_dividends

    def liquidate(self, common):
        """
        Liquidate account, compute capital gains, set balance to zero
        and returns real liquidation value.

        Parameters
        ----------
        common : Common
            instance of the class Common

        Returns
        -------
        float
            selling price
        """
        self.liquidation_non_taxable = self.price
        self.liquidation_cap_gains = self.balance - self.price
        self.balance = 0

    def reset(self):
        """
        Reset balance and capital gains to initial values.
        """
        self.balance = self.init_balance
        self.cap_gains = self.init_balance - self.price
