import numpy as np
import srpp
from CPR import annuities
from CPR import taxes
from CPR import tools
from CPR import balance_sheets


def simulate(job, common, prices):
    """
    Function that projects assets, RPPs and debts until the time of retirement.

    Parameters
    ----------
    job: tuple(Hhold, int)
        instance of the class Hhold and simulation number
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

        if check_liquidation(hh) or check_tax_unreg(hh):
            prepare_taxes(hh, year, common, prices)
            taxes.compute_after_tax_amount(hh, year, common, prices)

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
    Function that attaches to households stochastic processes on asset returns.

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
        d_returns[ret] = dict(zip(years,
                                  getattr(prices, f'ret_{ret}')[:, sim]))
    d_price_rent_ratio = dict(zip(years, prices.price_rent_ratio[:, sim]))

    return d_returns, d_price_rent_ratio


def prepare_wages(p, sim, common, prices):
    """
    Function that attaches wage profiles to individuals.

    Parameters
    ----------
    p: Person
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
    Function that creates a CPP/QPP account and enters past CPP/QPP contributions based on past wages.

    Parameters
    ----------
    p: Person
        instance of the class Person
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
    Function that computes age for a given year.

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
    Function that updates debt payments and balances.

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
    Function that adjusts contributions to all account types (RRSP, other registered, TFSA) and to pensions plans (DC and DB RPPs) so as to respect available contribution rooms.

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
            if p.age >= (p.init_age + int(p.replacement_rate_db
                                          / common.perc_year_db)):
                p.rpp_db.rate_employee_db = 0
        if not p.retired:
            p.contribution_room.compute_contributions(p, year, common, prices)


def update_assets(hh, year, d_returns, common, prices):
    """
    Function that updates assets every year.

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
    Function that manages the liquidation of assets upon retirement.

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
    nom = tools.create_nom(year, prices)

    for p in hh.sp:
        p.liquidation_non_taxable = 0
        p.liquidation_cap_gains = 0
        p.liquidation_cap_losses = 0
        p.liquidation_business_exempt = 0

    if year == getattr(hh, 'partial_ret_year', np.nan) - 1:
        unreg = hh.sp[0].fin_assets['unreg']
        unreg.liquidate()
        hh.sp[0].liquidation_non_taxable += unreg.liquidation_non_taxable
        hh.sp[0].liquidation_cap_gains += unreg.liquidation_cap_gains
        hh.sp[0].liquidation_cap_losses += unreg.liquidation_cap_losses

    if year == hh.ret_year - 1:
        for p in hh.sp:
            unreg = p.fin_assets['unreg']
            unreg.liquidate()
            p.liquidation_non_taxable += unreg.liquidation_non_taxable
            p.liquidation_cap_gains += unreg.liquidation_cap_gains
            p.liquidation_cap_losses += unreg.liquidation_cap_losses

        if common.sell_first_resid & ('first_residence' in hh.residences):
            first_res = hh.residences['first_residence']
            first_res.impute_rent(hh, year, common, prices)
            first_res.liquidate()
            liquidation_value = (first_res.liquidation_non_taxable
                                 + first_res.liquidation_cap_gains)
            if 'first_mortgage' in hh.debts:
                liquidation_value -= hh.debts['first_mortgage'].balance
                hh.debts['first_mortgage'].balance = 0
            for p in hh.sp:
                p.liquidation_non_taxable += (liquidation_value
                                              / (1 + hh.couple))

        if common.sell_second_resid & ('second_residence' in hh.residences):
            second_res = hh.residences['second_residence']
            second_res.liquidate()
            if 'second_mortgage' in hh.debts:
                second_res.liquidation_non_taxable -= (
                    hh.debts['second_mortgage'].balance)
                hh.debts['second_mortgage'].balance = 0
            for p in hh.sp:
                p.liquidation_non_taxable += (
                    second_res.liquidation_non_taxable / (1 + hh.couple))
                p.liquidation_cap_gains += (
                    second_res.liquidation_cap_gains / (1 + hh.couple))

        if common.sell_business & hasattr(hh, 'business'):
            hh.business.liquidate(common)
            liquidation_business_exempt = min(
                hh.business.liquidation_cap_gains, nom(common.lcge_real))
            for p in hh.sp:
                p.liquidation_non_taxable += (
                    hh.business.liquidation_non_taxable / (1 + hh.couple))
                p.liquidation_cap_gains += (
                    hh.business.liquidation_cap_gains / (1 + hh.couple))
                p.liquidation_business_exempt += (
                        liquidation_business_exempt / (1 + hh.couple))


def contribute_cpp(p, year, common):
    """
    Function that records CPP/QPP contributions.

    Parameters
    ----------
    p: Person
        instance of the class Person
    year : int
        year
    common : Common
        instance of the class Common
    """
    if (not p.retired) & (p.age < common.max_claim_age_cpp):
        p.cpp_account.MakeContrib(year, p.d_wages[year])


def claim_cpp(p):
    """
    Function to claim CPP/QPP benefits.

    Parameters
    ----------
    p: Person
        instance of the class Person
    """
    if p.age == p.claim_age_cpp:
        p.cpp_account.ClaimCPP(p.byear + p.claim_age_cpp)


def check_tax_unreg(hh):
    """
    Function that checks whether there are taxable returns to assets.

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
        if p.fin_assets['unreg'].income_to_tax:
            return True
    return False


def check_liquidation(hh):
    """
    Function to check whether there are liquidated assets to be taxed.

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
        p.liquidation_to_tax = (p.liquidation_non_taxable > 0 or
                                p.liquidation_cap_gains > 0 or
                                p.liquidation_cap_losses > 0 or
                                p.liquidation_business_exempt > 0)
    for p in hh.sp:
        if p.liquidation_to_tax:
            return True
    return False


def prepare_taxes(hh, year, common, prices):
    """
    Function to prepare the variables used in the SRD (in nominal terms).

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
        p.earn = p.d_wages[year]
        compute_rpp(p, nom, common)
        get_benefits_cpp(p, year, common)
        p.net_cap_gains = p.fin_assets['unreg'].withdrawal_cap_gains
        p.prev_cap_losses = p.fin_assets['unreg'].withdrawal_cap_losses
        p.div_elig = (common.share_div_elig
                      * p.fin_assets['unreg'].withdrawal_div)
        p.div_other_can = (hh.business.dividends_business / (1 + hh.couple)
                           if hasattr(hh, 'business') else 0)
        get_other_taxable(p, nom, common)
        get_other_non_taxable(p, nom)
        get_inc_rrsp(p, nom)
        get_contributions_assets(p, year, common)
        get_assets(p, common)


def get_assets(p, common):
    """
    Function to retrieve assets for social assistance asset test.

    Parameters
    ----------
    p: Person
        instance of the class Person
    common : Common
        instance of class Common
    """
    assets_unreg, assets_reg = 0, 0
    for acc in p.fin_assets:
        if acc == 'unreg':
            assets_unreg += p.fin_assets['unreg'].balance
        else:
            assets_reg += p.fin_assets[acc].balance
    p.assets = assets_unreg + max(0, assets_reg - common.exempt_soc_ass)

def compute_rpp(p, nom, common):
    """
    Compute rpp (DB and pension).

    Parameters
    ----------
    p: Person
        instance of the class Person
    nom: function
        function converting to nominal value
    common: Common
        instance of the class Common
    """
    p.rpp = nom(p.annuity_rpp_dc_real)
    if p.pension > 0:
        p.rpp += p.pension
    if hasattr(p, 'rpp_db') & p.retired & (p.age > common.db_minimum_age):
        p.rpp_db.compute_benefits(p, common)
        p.rpp += p.rpp_db.benefits


def get_benefits_cpp(p, year, common):
    """
    Function that computes annual CPP/QPP retirement benefits.

    s1 is the part of the supplementary benefit due to higher contribution rates in the 2019-2025 expansion; s2 is the part of the supplementary benefits attributable to changes in the YMPE; and PRB is for post-retirement benefits (for individuals who keep working after claiming -- this feature is not used in the CPR, since individuals automatically claim in the year they retire).

    Parameters
    ----------
    p: Person
        instance of the class Person
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


def get_inc_rrsp(p, nom):
    """
    Function that computes RRSP income from withdrawals.

    Parameters
    ----------
    p: Person
        instance of the class Person
    nom: function
        function converting to nominal value
    """
    p.inc_rrsp = nom(p.annuity_rrsp_real)

    if p.retired:
        return

    for acc in set(p.fin_assets) & set(('rrsp', 'other_reg')):
        p.inc_rrsp += p.fin_assets[acc].withdrawal


def get_other_taxable(p, nom, common):
    """
    Function that computes other taxable income.

    Parameters
    ----------
    p: Person
        instance of the class Person
    nom: function
        function converting to nominal value
    common : Common
        instance of the class Common
    """
    regular_div_and_int = (
        (1 - common.share_div_elig) * p.fin_assets['unreg'].withdrawal_div
        + p.fin_assets['unreg'].withdrawal_int)
    annuity_return = nom(p.annuity_non_rrsp_real - p.annuity_non_rrsp_0_real)
    p.other_taxable = regular_div_and_int + annuity_return


def get_other_non_taxable(p, nom):
    """
    Function that computes other non-taxable income.

    Parameters
    ----------
    p: Person
        instance of the class Person
    nom: function
        function converting to nominal value
    """
    withdrawal_non_tax = (p.fin_assets['unreg'].withdrawal_non_tax
                          + p.fin_assets['tfsa'].withdrawal)
    annuity_non_tax = nom(p.annuity_non_rrsp_0_real)

    p.other_non_taxable = withdrawal_non_tax + annuity_non_tax


def get_contributions_assets(p, year, common):
    """
    Function that computes contributions to registered and unregistered accounts (including DC and DB RPP).

    Parameters
    ----------
    p: Person
        instance of the class Person
    year : int
        year
    common : Common
        instance of the class Common
    """
    p.con_rrsp, p.con_non_rrsp = 0, 0

    if p.retired:
        return

    for acc in set(p.fin_assets):
        if acc in ['rrsp', 'other_reg']:
            p.con_rrsp += p.fin_assets[acc].contribution
        else:
            p.con_non_rrsp += p.fin_assets[acc].contribution
    if (p.rate_employee_db > 0) & (year < common.base_year
                                   + common.max_years_db):
        p.con_rrsp += p.rate_employee_db * p.d_wages[year]
    if hasattr(p, 'rpp_dc'):
        p.con_rrsp += p.contrib_employee_dc


def reset_accounts(hh):
    """
    Function that resets all variables to their initial values.

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
        for type in ['non_rrsp_0', 'non_rrsp', 'rpp_dc', 'rrsp']:
            setattr(p, f'annuity_{type}_real', 0)
    # cpp/qpp
        p.cpp_account.ResetCase()
        p.cpp = 0
