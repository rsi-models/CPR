import heapq
import numpy as np

class ContributionRoom:
    def __init__(self, init_room_rrsp, init_room_tfsa):
        self.init_room_rrsp = init_room_rrsp
        self.init_room_tfsa = init_room_tfsa
        self.reset()

    def compute_contributions(self, sp, year, common, prices):
        self.update_rrsp_room(sp, year, common)
        self.update_tfsa_room(sp, year, common)
        self.extra_contrib_rrsp = 0
        if (sp.replacement_rate_db > 0) & (year < common.base_year
                                           +common.max_years_db):
            self.adjust_db_contributions(sp, year, common)
        if hasattr(sp, 'rpp_dc'):
            self.adjust_dc_contributions(sp, year)
        for acc in set(sp.fin_assets) & set(('rrsp', 'other_reg')):
            self.adjust_rrsp_contributions(acc, sp, year)

        self.adjust_tfsa_contributions(sp, year, common, prices)

        self.adjust_unreg_contributions(sp, year)

    def update_rrsp_room(self, sp, year, common):
        if sp.age > common.max_age_no_rrif:
            self.room_rrsp = 0
        else:
            self.room_rrsp += min(common.perc_rrsp * sp.d_wages[year-1],
                                  common.d_rrsp_limit[year])

    def update_tfsa_room(self, sp, year, common):
        self.room_tfsa += common.d_tfsa_limit[year]
        self.room_tfsa += sp.fin_assets['tfsa'].withdrawal

    def adjust_db_contributions(self, sp, year, common):
        cpp_offset = (common.perc_cpp_2018
                      * min(sp.d_wages[year-1], common.d_ympe[year-1])
                      / common.max_years_db)
        benefits_earned = (sp.replacement_rate_db * sp.d_wages[year-1]
                            / common.max_years_db - cpp_offset)
        pension_credit = max(
            common.db_benefit_multiplier*benefits_earned - common.db_offset, 0)
        self.room_rrsp -= min(pension_credit, self.room_rrsp)

    def adjust_dc_contributions(self, sp, year):
        # transfer extra rpp_dc and rrsp contributions to tfsa:
        contrib = sp.rpp_dc.contrib_rate * sp.d_wages[year]
        if contrib <= self.room_rrsp:
            sp.rpp_dc.contribution = contrib
            self.room_rrsp -= contrib
        else:
            sp.rpp_dc.contribution = self.room_rrsp
            self.extra_contrib_rrsp += contrib - self.room_rrsp
            self.room_rrsp = 0
        self.adjust_employees_contributions(sp)

    def adjust_employees_contributions(self, sp):
        """
        Computes employee contribution to DC pension
        (used later to caculate taxes).
        """
        if sp.rpp_dc.contrib_rate == 0:
            sp.contrib_employee_dc = 0
        else:
            sp.contrib_employee_dc = (sp.rate_employee_dc /
                                        sp.rpp_dc.contrib_rate
                                        * sp.rpp_dc.contribution)

    def adjust_rrsp_contributions(self, acc, sp, year):
        contrib = sp.fin_assets[acc].contrib_rate*sp.d_wages[year]
        if contrib <= self.room_rrsp:
            sp.fin_assets[acc].contribution = contrib
            self.room_rrsp -= contrib
        else:
            sp.fin_assets[acc].contribution = self.room_rrsp
            self.extra_contrib_rrsp += contrib - self.room_rrsp
            self.room_rrsp = 0

    def adjust_tfsa_contributions(self, sp, year, common, prices):
        self.extra_contrib_tfsa = 0
        contrib = sp.fin_assets['tfsa'].contrib_rate * sp.d_wages[year]
        contrib += self.extra_contrib_rrsp
        if sp.age > common.max_age_no_rrif:
            contrib += self.adjust_rrif(sp, year, common, prices)

        if contrib <= self.room_tfsa:
            sp.fin_assets['tfsa'].contribution = contrib
            self.room_tfsa -= contrib
        else:
            sp.fin_assets['tfsa'].contribution = self.room_tfsa
            self.extra_contrib_tfsa += contrib - self.room_tfsa
            self.room_tfsa = 0

    def adjust_rrif(self, sp, year, common, prices):
        rrif_transfer_real = 0
        for acc in set(sp.fin_assets) & set(('rpp_dc', 'rrsp', 'other_reg')):
            rrif_transfer_real += sp.fin_assets[acc].rrif_withdrawal(sp, common)
        return rrif_transfer_real * prices.d_infl_factors[year]

    def adjust_unreg_contributions(self, sp, year):
        contrib = sp.fin_assets['unreg'].contrib_rate * sp.d_wages[year]
        contrib += self.extra_contrib_tfsa
        sp.fin_assets['unreg'].contribution = contrib

    def reset(self):
        self.room_rrsp = self.init_room_rrsp
        self.room_tfsa = self.init_room_tfsa


class FinAsset:
    """
    This class manages registered accounts.

    :type balance: float
    :param balance: Initia balance.

    :type contrib_rate: float
    :param contrib_rate: Annual contribution rate,
    in term of percentage of the household total wage.

    :type withdrawal: float
    :param withdrawal: Annual withdrawal

    :type mix_bills: float
    :param mix_bills: Proportion of assets invested in bills.

    :type mix_bonds: float
    :param mix_bonds: Proportion of assets invested in bonds.

    :type mix_equity: float
    :param mix_equity: Proportion of assets invested in equity.

    :type fee: float
    :param fee: Fee
    """

    def __init__(self, sp, hh, acc):
        self.init_balance = getattr(sp, f'bal_{acc}')
        self.contrib_rate = getattr(sp, f'cont_rate_{acc}')
        self.init_desired_withdrawal_real = getattr(sp, f'withdrawal_{acc}')
        self.mix_bills = hh.mix_bills
        self.mix_bonds = hh.mix_bonds
        self.mix_equity = hh.mix_equity
        self.fee = hh.fee
        self.reset()

    def update(self, d_returns, year, common, prices):
        """
        Updates the balance for contribution, withdrawal and growth.

        :type wage: float
        :param wage: Household total wage

        :type ret_bills: float
        :param retbills: Annual return on bills.

        :type ret_bonds: float
        :param ret_bonds: Annual return on bonds.

        :type ret_equity: float
        :param ret_equity: Annual return on equity
        """
        self.inflation_factor = prices.d_infl_factors[year]
        self.balance *= 1 + self.rate(d_returns, year)
        self.balance += self.contribution
        self.desired_withdrawal = (self.desired_withdrawal_real
                                   * self.inflation_factor)
        self.withdrawal = min(self.balance, self.desired_withdrawal)
        self.balance -= self.withdrawal

    def rate(self, d_returns, year):
        """
        Computes the rate of return.
        """
        return (self.mix_bills*d_returns['bills'][year]
                + self.mix_bonds*d_returns['bonds'][year]
                + self.mix_equity*d_returns['equity'][year] - self.fee)

    def rrif_withdrawal(self, sp, common):
        """
        Adjusts withdrawals to the mandatory minimum after 71 and returns
        the extra withdrawal required.
        """
        if self.balance > 0:
            extra_withdrawal_real = max(
                0, common.d_perc_rrif[sp.age]*self.balance_real
                - self.desired_withdrawal_real)
            self.desired_withdrawal_real += extra_withdrawal_real
        else:
            extra_withdrawal_real = 0

        return extra_withdrawal_real

    def liquidate(self):
        """
        Liquidates account,
        adjusts balance and returns liquidation value

        :rtype: float
        """
        value = self.balance
        self.balance, self.contribution, self.withdrawal = 0, 0, 0
        return value

    def reset(self):
        """
        Resets the balance to its initial balance.
        """
        self.balance = self.init_balance
        self.desired_withdrawal_real = self.init_desired_withdrawal_real
        self.withdrawal = 0  # to adjust contribution space tfsa

    @property
    def balance_real(self):
        """
        Computes real balance.
        """
        return self.balance / self.inflation_factor


class UnregAsset:
    """
    This class create a financial unregistered account.
    """
    def __init__(self, sp, hh, prices):
        self.init_balance = sp.bal_unreg
        self.contrib_rate = sp.cont_rate_unreg
        self.desired_withdrawal = sp.withdrawal_unreg
        self.init_cap_gains = sp.cap_gains_unreg
        self.init_realized_losses = sp.realized_losses_unreg
        self.mix_bills = hh.mix_bills
        self.mix_bonds = hh.mix_bonds
        self.mix_equity = hh.mix_equity
        self.fee = hh.fee
        self.fee_equity = hh.fee_equity
        self.ret_dividends = prices.ret_dividends
        self.init_inc_unreg_after_tax = 0
        self.reset()

    def update(self, d_returns, year, common, prices):
        """
        Updates the balance for contribution, withdrawal and growth.

        :type wage: float
        :param wage: Household total wage.

        :type ret_bills: float
        :param retbills: Annual return on bills.

        :type ret_bonds: float
        :param ret_bonds: Annual return on bonds.

        :type ret_equity: float
        :param ret_equity: Annual return on equity
        """
        self.inflation_factor = prices.d_infl_factors[year]
        self.compute_income(d_returns, year)
        self.update_balance()
        self.prepare_withdrawal()
        self.adjust_withdrawal_and_cap_gains()
        self.adjust_final_balance()
        self.amount_after_tax = 0
        self.amount_to_tax = (common.frac_cap_gains * self.cap_gains_withdrawal
                              + self.taxable_inc)

    def compute_income(self, d_returns, year):
        self.cap_gains_inc = (
            self.balance * self.mix_equity * (d_returns['equity'][year]
            - self.ret_dividends - self.fee_equity))
        self.taxable_inc = (self.balance * self.rate(d_returns, year)
                            - self.cap_gains_inc)

    def rate(self, d_returns, year):
        """
        Computes the rate of return.

        :type ret_bills: float
        :param retbills: Annual return on bills.

        :type ret_bonds: float
        :param ret_bonds: Annual return on bonds.

        :type ret_equity: float
        :param ret_equity: Annual return on equity

        :rtype: float
        """
        return (self.mix_bills*d_returns['bills'][year]
                + self.mix_bonds*d_returns['bonds'][year] +
                self.mix_equity*d_returns['equity'][year] - self.fee)

    def update_balance(self):
        self.non_taxable = self.balance - self.cap_gains
        self.non_taxable += self.after_tax_inc
        self.non_taxable += self.contribution
        self.cap_gains += self.cap_gains_inc
        self.taxable = self.taxable_inc
        self.balance = self.non_taxable + self.cap_gains + self.taxable

    def prepare_withdrawal(self):
        self.withdrawal = min(self.desired_withdrawal * self.inflation_factor,
                              self.balance)
        self.share_withdrawal = self.withdrawal / (self.balance + 1e-12)
        self.non_taxable_withdrawal = self.share_withdrawal * self.non_taxable
        self.cap_gains_withdrawal = self.share_withdrawal * self.cap_gains
        self.taxable_withdrawal = self.share_withdrawal * self.taxable

    def adjust_withdrawal_and_cap_gains(self):
        if self.cap_gains_withdrawal > 0:
            used_cap_losses = min(self.cap_gains_withdrawal,
                                  self.realized_losses)
            self.realized_losses -= used_cap_losses
            self.non_taxable_withdrawal += used_cap_losses
            self.cap_gains_withdrawal -= used_cap_losses
        else:
            self.realized_losses += (-self.cap_gains_withdrawal)
            self.non_taxable_withdrawal += self.cap_gains_withdrawal
            self.cap_gains_withdrawal = 0

    def adjust_final_balance(self):
        self.non_taxable *= (1 - self.share_withdrawal)
        self.cap_gains *= (1 - self.share_withdrawal)
        self.taxable = 0
        self.balance = self.non_taxable + self.cap_gains

    def compute_after_tax_inc(self):
        if self.amount_to_tax == 0:
            self.after_tax_share = 0
        else:
            self.after_tax_share = self.amount_after_tax / self.amount_to_tax

        self.after_tax_inc = ((1 - self.share_withdrawal)
                              * self.after_tax_share * self.taxable_inc)

    def compute_net_withdrawal(self, common):
        self.net_withdrawal = (
            self.non_taxable_withdrawal
            + self.after_tax_share * self.taxable_withdrawal
            + (1 - common.frac_cap_gains) * self.cap_gains_withdrawal
            + common.frac_cap_gains * self.after_tax_share
            * self.cap_gains_withdrawal)

    def prepare_liquidation(self, value_liquidation, cap_gains_liquidation,
                            common):
        """

        """
        self.amount_to_tax += common.frac_cap_gains * self.cap_gains
        self.non_taxable += (1-common.frac_cap_gains) * self.cap_gains
        self.cap_gains = 0

        self.amount_to_tax += common.frac_cap_gains * cap_gains_liquidation
        self.non_taxable += (value_liquidation
                             - common.frac_cap_gains * cap_gains_liquidation)
        self.balance = self.non_taxable

    def liquidate(self):
        value = self.balance + self.amount_after_tax - self.net_withdrawal
        self.balance, self.contribution, self.withdrawal = 0, 0, 0
        self.amount_to_tax, self.amount_after_tax, self.after_tax_inc = 0, 0, 0
        return value

    def reset(self):
        """
        Resets the nominal balance, capital gains capital losses and after
        tax income from unregistered account to their initial balances.
        """
        self.balance = self.init_balance
        self.cap_gains = self.init_cap_gains
        self.non_taxable = self.balance - self.cap_gains
        self.realized_losses = self.init_realized_losses
        self.after_tax_inc = 0
        self.net_withdrawal = 0


class RppDC(FinAsset):
    def __init__(self, sp, common):
        self.init_balance = sp.init_dc
        self.contrib_rate = sp.rate_employee_dc + sp.rate_employer_dc
        self.init_desired_withdrawal_real = 0
        self.mix_bills = common.mix_bills_rpp
        self.mix_bonds = common.mix_bonds_rpp
        self.mix_equity = common.mix_equity_rpp
        self.fee = common.fee_rpp
        self.reset()


class RppDB:
    """
    Manages defined benefits rpp.
    """
    def __init__(self, sp):
        self.init_rate_employee_db = sp.rate_employee_db
        self.replacement_rate_db = sp.replacement_rate_db
        self.income_previous_db = sp.income_previous_db
        self.reset()

    def compute_benefits(self, sp, common):
        """
        Computes rpp_db benefits and adjusts them for cpp.
        If rpp_db < cpp_qpp, rpp_db=0 when cpp_qpp starts.
        """
        if self.replacement_rate_db > 0:
            n = common.n_best_wages_db
            l_wages = [wage for wage in sp.d_wages.values()]
            self.mean_best_wage = sum(heapq.nlargest(n, l_wages)) / n

            years_service = sp.replacement_rate_db / common.perc_year_db
            if (years_service < common.max_years_db) and (sp.ret_age < common.db_ret_age_no_penalty):
                years_early_db = common.official_ret_age - sp.ret_age
            else:
                years_early_db = 0

            self.benefits_current_empl = (self.replacement_rate_db * self.mean_best_wage
                * (1 - years_early_db * common.db_penalty_early_ret))
            self.benefits += self.benefits_current_empl

            if sp.age >= common.official_ret_age:
                self.benefits -= min(self.compute_cpp_adjustment(sp, common),
                                     self.benefits_current_empl)
        if self.income_previous_db > 0:
            self.benefits += self.income_previous_db

    def compute_cpp_adjustment(self, sp, common):
        """
        Pension from current employer is adjusted for CPP benefits.
        Start in base year if enough years until retirement, otherwise goes
        backward from year before retirement.
        """
        years_db = int(self.replacement_rate_db / common.perc_year_db)

        if years_db <= sp.ret_year - common.base_year:
            mean_wage = np.mean([min(sp.d_wages[common.base_year +  t],
                                     common.d_ympe[common.base_year +  t])
                                 for t in range(years_db)])
        else:
            mean_wage = np.mean([min(sp.d_wages[sp.ret_year - t],
                                     common.d_ympe[sp.ret_year - t])
                                 for t in range(1, years_db + 1)])

        return (common.perc_cpp_2018 * years_db / common.max_years_db
                * mean_wage)

    def reset(self):
        self.benefits = 0
        self.rate_employee_db = self.init_rate_employee_db


class RealAsset:
    """
    This class updates the balance of a residence
    given the growth rate in prices
    """

    def __init__(self, d_hh, resid):
        self.init_balance = d_hh[resid]
        self.price = d_hh[f'price_{resid}']
        self.reset()

    def grow(self, growth_rates, year, prices):
        """
        Updates housing balance.

        :type growth_rate: float
        :param growth_rate: Groth rate
        """
        self.inflation_factor = prices.d_infl_factors[year]
        self.balance *= 1 + growth_rates[year]

    def liquidate(self):
        """
        Liquidates the account, adjusts balance
        and returns real liquidation value
        :rtype: float
        """
        self.sell_value = self.balance
        self.cap_gains = self.balance - self.price
        self.balance = 0

    def reset(self):
        """
        Resets the balance to its initial balance and capital gains to zero.
        """
        self.balance = self.init_balance
        self.cap_gains = 0


class Business:
    """
    This class creates a business.

    :type balance: float
    :param balance: Initia balance.

    :type cap_gains: float
    :param cap_gains: Initial capital gains.

    :type realized_losses: float
    :param realized_losses: Initial capital losses.

    :type ret_dividends:
    :param ret_dividends:
    """

    def __init__(self, d_hh):
        self.init_balance = d_hh['business']
        self.price = d_hh['price_business']
        self.reset()

    def update(self, ret, year, prices):
        """
        Updates housing balance.

        :type growth_rate: float
        :param growth_rate: Groth rate
        """
        self.inflation_factor = prices.d_infl_factors[year]
        self.dividends_business = self.balance * prices.ret_dividends
        self.balance *= 1 + ret[year] - prices.ret_dividends

    def liquidate(self, common):
        """
        Liquidates the account, adjusts balance
        and returns real liquidation value
        :rtype: float
        """
        self.selling_price = self.balance
        business_exempt = common.business_exempt_real * self.inflation_factor
        self.cap_gains = max(self.balance - business_exempt, 0)
        self.balance = 0
        return self.selling_price

    def reset(self):
        """
        Resets the nominal balance, capital gains capital losses and after
        tax income from unregistered account to their initial balances.
        """
        self.balance = self.init_balance
        self.cap_gains = self.init_balance - self.price
