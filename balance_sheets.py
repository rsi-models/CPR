import tools
import taxes
import simulator
import importlib
importlib.reload(taxes)
importlib.reload(simulator)


def compute_bs_bef_ret(hh, year, common, prices):
    """
    Compute pre-retirement balance sheet.

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
    nom_2018 = tools.create_nom(year, prices)

    hh_tax = taxes.file_household(hh, year, common, prices)
    for p in hh_tax.sp:
        p.net_income_bef_ret = (p.fin_assets['unreg'].net_withdrawal +
                                nom_2018(p.disp_inc))
    compute_cons_bef_ret(hh, year, prices)


def compute_cons_bef_ret(hh, year, prices):
    """
    Compute pre-retirement consumption.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    prices : Prices
        instance of the class Prices
    """
    real = tools.create_real(year, prices)

    hh.net_income_bef_ret = sum([sp.net_income_bef_ret for p in hh.sp])
    hh.contributions = sum([sp.contributions_rrsp + p.contributions_non_rrsp
                            for p in hh.sp])
    hh.debt_payments = sum([hh.debts[debt].payment for debt in hh.debts])
    hh.cons_bef_ret_real = real(hh.net_income_bef_ret - hh.contributions
                                - hh.debt_payments)


def add_output(hh, year, prices, key):
    """
    Extract output variables.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    prices : Prices
        instance of the class Prices
    key : str
        before ("bef") or after ("aft")
    """
    real = tools.create_real(year, prices)

    for p in hh.sp:
        hh.d_output[f'{sp.who}wage_{key}'] = real(p.d_wages[year])
        hh.d_output[f'{sp.who}pension_{key}'] = real(p.pension)

    for residence in hh.residences:
        hh.d_output[f'{residence}_{key}'] = real(hh.residences[residence].balance)
    if hasattr(hh, 'business'):
        hh.d_output[f'business_{key}'] = real(hh.business.balance)
    if 'first_mortgage' in hh.debts:
        hh.d_output[f'first_mortgage_balance_{key}'] = \
            real(hh.debts['first_mortgage'].balance)

    if key == 'bef':
        hh.d_output[f'net_income_{key}'] = real(hh.net_income_bef_ret)
        hh.d_output[f'cons_{key}'] = hh.cons_bef_ret_real

    if key in ['bef', 'part']:
        for p in hh.sp:
            if hasattr(p, 'rpp_dc'):
                hh.d_output[f'{sp.who}rpp_dc_{key}'] = real(p.rpp_dc.balance)
            for acc in p.fin_assets:
                hh.d_output[f'{sp.who}{acc}_balance_{key}'] = \
                    real(p.fin_assets[acc].balance)

    if key in ['bef', 'after']:
        hh.d_output[f'debt_payments_{key}'] = real(hh.debt_payments)

    if key in ['part', 'after']:
        for p in hh.sp:
            hh.d_output[f'{sp.who}annuity_rrsp_{key}'] = p.annuity_rrsp_real
            hh.d_output[f'{sp.who}annuity_dc_{key}'] = p.annuity_rpp_dc_real
            hh.d_output[f'{sp.who}annuity_tfsa_{key}'] = p.annuity_tfsa_real
            hh.d_output[f'{sp.who}annuity_unreg_{key}'] = p.annuity_unreg_real

    if key == 'after':
        hh.d_output[f'net_income_{key}'] = real(hh.net_income_after_ret)
        hh.d_output[f'cons_{key}'] = hh.cons_after_ret_real

        for p in hh.sp:
            hh.d_output[f'{sp.who}years_to_retire'] = p.ret_age - p.init_age
            hh.d_output[f'{sp.who}factor'] = p.factor
            hh.d_output[f'{sp.who}cpp_{key}'] = real(p.cpp)
            hh.d_output[f'{sp.who}gis_{key}'] = real(p.inc_gis)
            hh.d_output[f'{sp.who}oas_{key}'] = real(p.inc_oas)
            if hasattr(p, 'rpp_db'):
                hh.d_output[f'{sp.who}rpp_db_benefits_{key}'] = \
                    real(p.rpp_db.benefits)


def compute_bs_after_ret(hh, year, common, prices):
    """
    Compute post-retirement balance-sheet.

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
    nom, real = tools.create_nom_real(year, prices)
    nom_2018 = tools.create_nom(year, prices)

    hh_tax = taxes.file_household(hh, year, common, prices)
    hh.net_income_after_ret = nom_2018(common.tax.haftertax(hh_tax))
    taxes.get_gis_oas(hh, hh_tax, year, prices)

    hh.debt_payments = sum([hh.debts[debt].payment for debt in hh.debts])
    hh.cons_after_ret_real = real(hh.net_income_after_ret - hh.debt_payments)
    if hasattr(hh, 'imputed_rent_real'):
        hh.cons_after_ret_real -= nom(hh.imputed_rent_real)
