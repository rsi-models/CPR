import importlib
import numpy as np
from cpp import cpp
import annuities
import taxes
import tools
import balance_sheets
importlib.reload(annuities)
importlib.reload(taxes)
importlib.reload(balance_sheets)


def simulate(job, common, prices):
    """
    Projects RPP, assets and debts to retirement (and partial retirement)

    :type hh: object
    :param hh: Instance of the initialisation.Household class.

    :type common: object
    :param common: Instance of the macro.Common class

    :type prices: object
    :param prices: Object of the macro.Prices class

    :type sim: integer
    :param sim: Simulation identification
    """
    hh, sim = job


    # store output in dictionary:
    hh.d_output = dict(hh_index=hh.index, sim=sim)

    d_returns, prices.d_price_rent_ratio = extract_time_series(sim, common,
                                                               prices)

    for sp in hh.sp:
        prepare_wages(sp, sim, common, prices)
        initialize_cpp_account(sp, hh, common)

    year = common.base_year
    while year < hh.ret_year:
        update_ages(hh, year)
        update_debts(hh, year, sim, common, prices)
        manage_contributions(hh, year, common, prices)
        update_assets(hh, year, d_returns, common, prices)
        manage_liquidations(hh, year, common, prices)

        for sp in hh.sp:
            contribute_cpp(sp, year, common)
            claim_cpp(sp)

        if check_tax_unreg(hh):
            tax_unreg_inc(hh, year, common, prices)

        if year == hh.cons_bef_ret_year:
            prepare_taxes(hh, year, common, prices)
            balance_sheets.compute_bs_bef_ret(hh, year, common, prices)
            balance_sheets.add_output(hh, year, prices, 'bef')

        # partial retirement (some couples)
        if year == getattr(hh, 'partial_ret_year', np.nan) - 1:
            annuities.compute_partial_annuities(hh, d_returns, year, prices)
        if year == getattr(hh, 'partial_ret_year', np.nan):
            balance_sheets.add_output(hh, year, prices, 'part')

        # full retirement
        if year == hh.ret_year - 1:
            annuities.compute_annuities(hh, d_returns, year, prices)

        year += 1

    while True:
        update_ages(hh, year)
        update_debts(hh, year, sim, common, prices)
        for sp in hh.sp:
            claim_cpp(sp)
        if year == hh.cons_after_ret_year:
            break
        year += 1

    prepare_taxes(hh, year, common, prices)
    balance_sheets.compute_bs_after_ret(hh, year, common, prices)
    balance_sheets.add_output(hh, year, prices, 'after')

    # reset assets, debts and annuities
    reset_accounts(hh)

    return hh.d_output

def extract_time_series(sim, common, prices):
    d_returns = {}
    for ret in ['bills', 'bonds', 'equity', 'housing', 'business']:
        years = range(common.base_year, common.base_year + common.future_years)
        d_returns[ret] = dict(zip(years, getattr(prices, f'ret_{ret}')[:, sim]))
    d_price_rent_ratio = dict(zip(years, prices.price_rent_ratio[:, sim]))

    return d_returns, d_price_rent_ratio


def prepare_wages(sp, sim, common, prices):
    time_range = range(sp.byear + common.min_age_cpp,
                       sp.byear + common.future_years)
    sp.d_wages = dict(zip(time_range, sp.wage_profile[:, sim]))
    sp.d_wages = {year: sp.d_wages[year] * prices.d_infl_factors[year]
                  for year in sp.d_wages}


def initialize_cpp_account(sp, hh, common):

    rules = common.rules_qpp if hh.prov == 'qc' else common.rules_cpp
    sp.cpp_account = cpp.account(sp.byear, rules)

    for year in range(sp.byear + common.min_age_cpp, sp.byear + sp.age):
        sp.cpp_account.MakeContrib(year, sp.d_wages[year])


def update_ages(hh, year):
    """
    Compute the age for a given year

    :type hh: object
    :param hh: Instance of the initialisation.Household class.

    :type year: integer
    :param year: Year
    """
    for sp in hh.sp:
        sp.age = year - sp.byear


def update_debts(hh, year, sim, common, prices):
    """
    Closes debt accounts that are repaid
    and updates debts payments and balances.

    :type hh: object
    :param hh: Instance of the initialisation.Household class.

    :type common: object
    :param common: Instance of the macro.Common class.

    :type prices: object
    :param prices: Object of the macro.Prices class.

    :type sim: integer
    :param sim: Simulation identification.

    :type t: integer
    :param t: Period identification.
    """
    for debt in hh.debts:
        hh.debts[debt].update(
            year, prices.d_interest_debt[debt][year-common.base_year, sim],
            prices)

def manage_contributions(hh, year, common, prices):
    for sp in hh.sp:
        if (sp.replacement_rate_db > 0):
            if (sp.age >= sp.init_age
                          + int(sp.replacement_rate_db/common.perc_year_db)):
                sp.rpp_db.rate_employee_db = 0
        if not sp.retired:
            sp.contribution_room.compute_contributions(sp, year, common, prices)

def update_assets(hh, year, d_returns, common, prices):
    """
    Updates assets.
    """

    for sp in hh.sp:
        if sp.retired:
            continue

        if hasattr(sp, 'rpp_dc'):
            sp.rpp_dc.update(d_returns, year, common, prices)
        for acc in sp.fin_assets:
            sp.fin_assets[acc].update(d_returns, year, common, prices)
    for acc in hh.residences:
        hh.residences[acc].grow(d_returns['housing'], year, prices)
    if hasattr(hh, 'business'):
        hh.business.update(d_returns['business'], year, prices)


def manage_liquidations(hh, year, common, prices):

    if year == getattr(hh, 'partial_ret_year', np.nan) - 1:
        hh.sp[0].fin_assets['unreg'].prepare_liquidation(0, 0, common)

    if year == hh.ret_year - 1:
        value_liquidation, cap_gains_liquidation = \
            annuities.liquidate_real_assets(hh, year, common, prices)
        for sp in hh.sp:
            sp.fin_assets['unreg'].prepare_liquidation(
                value_liquidation / (1 + hh.couple),
                cap_gains_liquidation / (1 + hh.couple), common)


def contribute_cpp(sp, year, common):
    if (not sp.retired) & (sp.age < common.max_claim_age_cpp):
        sp.cpp_account.MakeContrib(year, sp.d_wages[year])


def claim_cpp(sp):
    if sp.age == sp.claim_age_cpp:
        sp.cpp_account.ClaimCPP(sp.byear + sp.claim_age_cpp)


def check_tax_unreg(hh):
    for sp in hh.sp:
        if sp.fin_assets['unreg'].amount_to_tax > 0:
            return True
    return False


def tax_unreg_inc(hh, year, common, prices):
    prepare_taxes(hh, year, common, prices)
    taxes.compute_after_tax_amount(hh, year, common, prices)


def prepare_taxes(hh, year, common, prices):
    """
    Prepares variables used in simtax (in nominal terms).
    """
    nom = tools.create_nom(year, prices)

    for sp in hh.sp:
        compute_benefits_rpp_db(sp, common)
        get_benefits_cpp(sp, year, common)
        get_contributions_cpp(sp, common)
        get_contributions_assets(sp, year, common)
        get_withdrawals(sp)

        sp.earn = sp.d_wages[year]
        if hasattr(hh, 'business'):
            sp.earn += hh.business.dividends_business / (1 + hh.couple)

        sp.con_rrsp = sp.contributions_rrsp
        sp.inc_rrsp = nom(sp.annuity_rrsp_real) + sp.withdrawal_rrsp

        sp.rpp = nom(sp.annuity_rpp_dc_real)
        if sp.pension > 0:
            sp.rpp += sp.pension
        if hasattr(sp, 'rpp_db'):
            sp.rpp += sp.rpp_db.benefits

        sp.othtax = 0
        sp.othntax = sp.withdrawal_tfsa
        sp.othntax += nom(sp.annuity_tfsa_real + sp.annuity_unreg_real)

        sp.annuity_return = nom((sp.annuity_tfsa_real - sp.annuity_tfsa_0_real)
            + (sp.annuity_unreg_real - sp.annuity_unreg_0_real))
        sp.othtax += sp.annuity_return
        sp.othntax -= sp.annuity_return


def compute_benefits_rpp_db(sp, common):
    """
    Computes rpp_db benefits and adjusts them for cpp.
    If rpp_db < cpp_qpp, rpp_db=0 when cpp_qpp starts.
    """
    if hasattr(sp, 'rpp_db') & sp.retired & (sp.age > common.db_minimum_age):
        sp.rpp_db.compute_benefits(sp, common)


def get_benefits_cpp(sp, year, common):
    """
    Gets CPP benefits. s1 is the increase due to higher contribution rates,
    s2 is the increase due to changes in brackets
    and prb is for post retirement benefit
    (after claiming but still contributing).
    """
    sp.cpp = 12 * (
        sp.cpp_account.gBenefit(year)
        + sp.cpp_account.gBenefit_s1(year) + sp.cpp_account.gBenefit_s2(year)
        + sp.cpp_account.gPRB(year)
        + sp.cpp_account.gPRB_s1(year) + sp.cpp_account.gPRB_s2(year))

    if common.old_cpp:
        sp.cpp -= 12 * (
            sp.cpp_account.gBenefit_s1(year) + sp.cpp_account.gBenefit_s2(year)
            + sp.cpp_account.gPRB_s1(year) + sp.cpp_account.gPRB_s2(year))


def get_contributions_cpp(sp, common):
    """
    Gets CPP contributions. s1 is the increase in contribution rates,
    s2 is the increase in brackets and prb is for post retirement benefit
    (after claiming but still contributing).
    """
    if sp.age > common.max_age_cpp:
        sp.cpp_contrib = 0
        return

    min_age = common.min_age_cpp
    sp.cpp_contrib = (sp.cpp_account.history[sp.age - min_age].contrib
                      + sp.cpp_account.history[sp.age - min_age].contrib_s1
                      + sp.cpp_account.history[sp.age - min_age].contrib_s2)
    if common.old_cpp:
        sp.cpp_contrib -= (
            sp.cpp_account.history[sp.age - min_age].contrib_s1
            + sp.cpp_account.history[sp.age - min_age].contrib_s2)


def get_contributions_assets(sp, year, common):
    """
    Get total annual contributions to registered and unregistered accounts
    made by a member of the household. Contributions to DB pension for 35 years.
    """

    sp.contributions_rrsp, sp.contributions_non_rrsp = 0, 0

    if sp.retired:
        return
    for acc in set(sp.fin_assets):
        if acc in ['rrsp', 'other_reg']:
            sp.contributions_rrsp += sp.fin_assets[acc].contribution
        else:
            sp.contributions_non_rrsp += sp.fin_assets[acc].contribution
    if (sp.rate_employee_db > 0) & (year < common.base_year
                                    +common.max_years_db):
        sp.contributions_rrsp += sp.rate_employee_db*sp.d_wages[year]
    if hasattr(sp, 'rpp_dc'):
        sp.contributions_rrsp += sp.contrib_employee_dc


def get_withdrawals(sp):
    """
    Get total annual withdrawalst from registered and unregistered accounts
    made by a member of the household.

    :type hh: object
    :param hh: Instance of the initialisation.Household class.

    :type sp: object
    :param sp: Instance of the initialisation.Person class.

    :type s: float
    :param s: share of total wages
    """

    sp.withdrawal_rrsp, sp.withdrawal_tfsa = 0, 0

    if sp.retired:
        return

    for acc in sp.fin_assets:
        if acc in ['rrsp', 'other_reg']:
            sp.withdrawal_rrsp += sp.fin_assets[acc].withdrawal
        if acc in ['tfsa']:
            sp.withdrawal_tfsa += sp.fin_assets[acc].withdrawal


def reset_accounts(hh):
    """
    Resets all accounts

    :type hh: object
    :param hh: Instance of the initialisation.Household class.
    """
    for sp in hh.sp:
        sp.age = sp.init_age
        sp.retired = False
        sp.contribution_room.reset()
        # assets:
        if hasattr(sp, 'rpp_dc'):
            sp.rpp_dc.reset()
        if hasattr(sp, 'rpp_db'):
            sp.rpp_db.reset()
        for acc in sp.fin_assets:
            sp.fin_assets[acc].reset()
    for acc in hh.residences:
        hh.residences[acc].reset()
    if hasattr(hh, 'business'):
        hh.business.reset()
    # debts
    for debt in hh.debts:
        hh.debts[debt].reset()
    # annuities
    for sp in hh.sp:
        for acc in ['rrsp', 'rpp_dc', 'tfsa', 'tfsa_0', 'unreg', 'unreg_0',
                    'return']:
            setattr(sp, f'annuity_{acc}_real', 0)
    # cpp/qpp
        sp.cpp_account.ResetCase()
        sp.cpp = 0
