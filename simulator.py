import importlib
import numpy as np
import srpp
from CPR import annuities
from CPR import taxes
from CPR import tools
from CPR import balance_sheets
importlib.reload(annuities)
importlib.reload(taxes)
importlib.reload(balance_sheets)


def simulate(job, common, prices):
    """
    Project assets, RPPs, debt to retirement.

    Parameters
    ----------
    common: Common
        instance of the class Common
    prices: Prices
        instance of the class Prices

    Returns
    -------
    dict:
        dictionary containing households' characteristics
        before and after retirement
    """
    hh, sim = job

    # store output in dictionary:
    hh.d_output = dict(hh_index=hh.index, sim=sim)

    d_returns, prices.d_price_rent_ratio = extract_time_series(sim, common,
                                                               prices)

    for p in hh.sp:
        prepare_wages(p, sim, common, prices)
        initialize_cpp_account(p, hh, common)

    year = common.base_year
    while year < hh.ret_year:
        update_ages(hh, year)
        update_debts(hh, year, sim, common, prices)
        adjust_contributions(hh, year, common, prices)
        update_assets(hh, year, d_returns, common, prices)
        manage_liquidations(hh, year, common, prices)

        for p in hh.sp:
            contribute_cpp(p, year, common)
            claim_cpp(p)

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
        for p in hh.sp:
            claim_cpp(p)
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
    """
    Attach stochastic processes on asset returns to households.

    Parameters
    ----------
    sim : int
        simulation number
    common : Common
        instance of the class Common
    prices : Prices
        instance of the class Prices

    Returns
    -------
    dict
        returns on assets
    dict
        price-rent ratio
    """
    d_returns = {}
    for ret in ['bills', 'bonds', 'equity', 'housing', 'business']:
        years = range(common.base_year, common.base_year + common.future_years)
        d_returns[ret] = dict(zip(years, getattr(prices, f'ret_{ret}')[:, sim]))
    d_price_rent_ratio = dict(zip(years, prices.price_rent_ratio[:, sim]))

    return d_returns, d_price_rent_ratio


def prepare_wages(p, sim, common, prices):
    """
    Attach wage profiles to people.

    Parameters
    ----------
    p : Person
        instance of the class Person
    sim : int
        simulation number
    common : Common
        instance of the class Common
    prices: Prices
        instance of the class Prices
    """
    time_range = range(p.byear + common.min_age_cpp,
                       p.byear + common.future_years)
    p.d_wages = dict(zip(time_range, p.wage_profile[:, sim]))
    p.d_wages = {year: p.d_wages[year] * prices.d_infl_factors[year]
                 for year in p.d_wages}


def initialize_cpp_account(p, hh, common):
    """
    Create cpp account and enter past contributions based on wages.

    Parameters
    ----------
    p : Person
        spouse in household 
    hh: Hhold
        household
    common : Common
        instance of the class Common
    """

    rules = common.rules_qpp if hh.prov == 'qc' else common.rules_cpp
    p.cpp_account = srpp.account(p.byear, rules)

    for year in range(p.byear + common.min_age_cpp, p.byear + p.age):
        p.cpp_account.MakeContrib(year, p.d_wages[year])


def update_ages(hh, year):
    """
    Compute age for a given year.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    """
    for p in hh.sp:
        p.age = year - p.byear


def update_debts(hh, year, sim, common, prices):
    """
    Update debts' payments and balances.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    sim : int
        simulation number
    common : Common
        instance of the class Common
    prices: Prices
        instance of the class Prices
    """
    for debt in hh.debts:
        hh.debts[debt].update(
            year, prices.d_interest_debt[debt][year - common.base_year, sim],
            prices)

def adjust_contributions(hh, year, common, prices):
    """
    Adjust contributions to all types of accounts (RRSP, TFSA, etc)
    to respect contribution rooms.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    common : Common
        instance of the class Common
    prices: Prices
        instance of the class Prices
    """
    for p in hh.sp:
        if (p.replacement_rate_db > 0):
            if (p.age >= p.init_age
                         + int(p.replacement_rate_db / common.perc_year_db)):
                p.rpp_db.rate_employee_db = 0
        if not p.retired:
            p.contribution_room.compute_contributions(p, year, common, prices)

def update_assets(hh, year, d_returns, common, prices):
    """
    Update assets.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    d_returns : dict
        dictionary of returns
    common : Common
        instance of the class Common
    prices: Prices
    instance of the class Prices
    """

    for p in hh.sp:
        if p.retired:
            continue

        if hasattr(p, 'rpp_dc'):
            p.rpp_dc.update(d_returns, year, common, prices)
        for acc in p.fin_assets:
            p.fin_assets[acc].update(d_returns, year, common, prices)
    for acc in hh.residences:
        hh.residences[acc].update(d_returns['housing'], year, prices)
    if hasattr(hh, 'business'):
        hh.business.update(d_returns['business'], year, prices)


def manage_liquidations(hh, year, common, prices):
    """
    Manage liquidation of assets before retirement.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    common : Common
        instance of the class Common
    prices: Prices
        instance of the class Prices
    """
    if year == getattr(hh, 'partial_ret_year', np.nan) - 1:
        hh.sp[0].fin_assets['unreg'].prepare_liquidation(0, 0, common)

    if year == hh.ret_year - 1:
        value_liquidation, cap_gains_liquidation = \
            annuities.liquidate_real_assets(hh, year, common, prices)
        for p in hh.sp:
            p.fin_assets['unreg'].prepare_liquidation(
                value_liquidation / (1 + hh.couple),
                cap_gains_liquidation / (1 + hh.couple), common)


def contribute_cpp(p, year, common):
    """
    Record cpp contributions.

    Parameters
    ----------
    p : Person
        spouse in household 
    year : int
        year
    common : Common
        instance of the class Common
    """
    if (not p.retired) & (p.age < common.max_claim_age_cpp):
        p.cpp_account.MakeContrib(year, p.d_wages[year])


def claim_cpp(p):
    """
    Claim CPP benefits.

    Parameters
    ----------
    p : Person
        spouse in household 
    """
    if p.age == p.claim_age_cpp:
        p.cpp_account.ClaimCPP(p.byear + p.claim_age_cpp)


def check_tax_unreg(hh):
    """
    Check if there are taxable returns to assets.

    Parameters
    ----------
    hh: Hhold
        household

    Returns
    -------
    bool
        True or False
    """
    for p in hh.sp:
        if p.fin_assets['unreg'].amount_to_tax > 0:
            return True
    return False


def tax_unreg_inc(hh, year, common, prices):
    """
    Tax unregistered assets.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    common : Common
        instance of the class Common
    prices: Prices
        instance of the class Prices
    """
    prepare_taxes(hh, year, common, prices)
    taxes.compute_after_tax_amount(hh, year, common, prices)


def prepare_taxes(hh, year, common, prices):
    """
    Prepare variables used in srd (in nominal terms).

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    common : Common
        instance of the class Common
    prices : Prices
        instance of the class Prices
    """
    nom = tools.create_nom(year, prices)

    for p in hh.sp:
        compute_benefits_rpp_db(p, common)
        get_benefits_cpp(p, year, common)
        get_contributions_cpp(p, common)
        get_contributions_assets(p, year, common)
        get_withdrawals(p)

        p.earn = p.d_wages[year]
        p.div_other_can = 0
        if hasattr(hh, 'business'):
            p.div_other_can = hh.business.dividends_business / (1 + hh.couple)

        p.con_rrsp = p.contributions_rrsp
        p.inc_rrsp = nom(p.annuity_rrsp_real) + p.withdrawal_rrsp

        p.rpp = nom(p.annuity_rpp_dc_real)
        if p.pension > 0:
            p.rpp += p.pension
        if hasattr(p, 'rpp_db'):
            p.rpp += p.rpp_db.benefits

        p.othtax = 0
        p.othntax = p.withdrawal_tfsa
        p.othntax += nom(p.annuity_tfsa_real + p.annuity_unreg_real)

        p.annuity_return = nom((p.annuity_tfsa_real - p.annuity_tfsa_0_real)
            + (p.annuity_unreg_real - p.annuity_unreg_0_real))
        p.othtax += p.annuity_return
        p.othntax -= p.annuity_return


def compute_benefits_rpp_db(p, common):
    """
    Compute RPP DB benefits and adjust them for CPP/QPP benefits.
    If RPP DB < CPP benefits, RPP DB = 0 when CPP starts.

    Parameters
    ----------
    p : Person
        spouse in household 
    common : Common
        instance of the class Common
    """
    if hasattr(p, 'rpp_db') & p.retired & (p.age > common.db_minimum_age):
        p.rpp_db.compute_benefits(p, common)


def get_benefits_cpp(p, year, common):
    """
    Compute annual CPP benefits. 
    s1 is the increase due to higher contribution rates,
    s2 is the increase due to changes in ympe
    and PRB is for post retirement benefit (after claiming but still contributing).

    Parameters
    ----------
    p : Person
        spouse in household 
    year : int
        year
    common : Common
        instance of the class Common
    """
    p.cpp = 12 * (
        p.cpp_account.gBenefit(year)
        + p.cpp_account.gBenefit_s1(year) + p.cpp_account.gBenefit_s2(year)
        + p.cpp_account.gPRB(year)
        + p.cpp_account.gPRB_s1(year) + p.cpp_account.gPRB_s2(year))

    if common.old_cpp:
        p.cpp -= 12 * (
            p.cpp_account.gBenefit_s1(year) + p.cpp_account.gBenefit_s2(year)
            + p.cpp_account.gPRB_s1(year) + p.cpp_account.gPRB_s2(year))


def get_contributions_cpp(p, common):
    """
    Compute CPP contributions. s1 is the increase in contribution rates,
    s2 is the increase in brackets and PRB is for post retirement benefit
    (after claiming but still contributing).

    Parameters
    ----------
    p : Person
        spouse in household 
    common : Common
        instance of the class Common
    """
    if p.age > common.max_age_cpp:
        p.cpp_contrib = 0
        return

    min_age = common.min_age_cpp
    p.cpp_contrib = (p.cpp_account.history[p.age - min_age].contrib
                      + p.cpp_account.history[p.age - min_age].contrib_s1
                      + p.cpp_account.history[p.age - min_age].contrib_s2)
    if common.old_cpp:
        p.cpp_contrib -= (
            p.cpp_account.history[p.age - min_age].contrib_s1
            + p.cpp_account.history[p.age - min_age].contrib_s2)


def get_contributions_assets(p, year, common):
    """
    Compute contributions to registered and unregistered accounts
    (including DC and DB RPP).

    Parameters
    ----------
    p : Person
        spouse in household 
    year : int
        year
    common : Common
        instance of the class Common
    """
    p.contributions_rrsp, p.contributions_non_rrsp = 0, 0

    if p.retired:
        return
    for acc in set(p.fin_assets):
        if acc in ['rrsp', 'other_reg']:
            p.contributions_rrsp += p.fin_assets[acc].contribution
        else:
            p.contributions_non_rrsp += p.fin_assets[acc].contribution
    if (p.rate_employee_db > 0) & (year < common.base_year
                                   + common.max_years_db):
        p.contributions_rrsp += p.rate_employee_db * p.d_wages[year]
    if hasattr(p, 'rpp_dc'):
        p.contributions_rrsp += p.contrib_employee_dc


def get_withdrawals(p):
    """
    Compute withdrawals from RRSP and TFSA.

    Parameters
    ----------
    p : Person
        spouse in household 
    """

    p.withdrawal_rrsp, p.withdrawal_tfsa = 0, 0

    if p.retired:
        return

    for acc in p.fin_assets:
        if acc in ['rrsp', 'other_reg']:
            p.withdrawal_rrsp += p.fin_assets[acc].withdrawal
        if acc in ['tfsa']:
            p.withdrawal_tfsa += p.fin_assets[acc].withdrawal


def reset_accounts(hh):
    """
    Reset all variables to their initial values.

    Parameters
    ----------
    hh: Hhold
        household
    """
    for p in hh.sp:
        p.age = p.init_age
        p.retired = False
        p.contribution_room.reset()
        # assets:
        if hasattr(p, 'rpp_dc'):
            p.rpp_dc.reset()
        if hasattr(p, 'rpp_db'):
            p.rpp_db.reset()
        for acc in p.fin_assets:
            p.fin_assets[acc].reset()
    for acc in hh.residences:
        hh.residences[acc].reset()
    if hasattr(hh, 'business'):
        hh.business.reset()
    # debts
    for debt in hh.debts:
        hh.debts[debt].reset()
    # annuities
    for p in hh.sp:
        for acc in ['rrsp', 'rpp_dc', 'tfsa', 'tfsa_0', 'unreg', 'unreg_0',
                    'return']:
            setattr(p, f'annuity_{acc}_real', 0)
    # cpp/qpp
        p.cpp_account.ResetCase()
        p.cpp = 0
