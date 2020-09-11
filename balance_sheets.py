from CPR import tools
from CPR import taxes
from CPR import simulator
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
    nom = tools.create_nom(year, prices)

    hh_srd = taxes.file_household(hh, year, common, prices)

    for who, p in enumerate(hh.sp):
        p.disp_inc_bef_ret = nom(hh_srd.sp[who].disp_inc)
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

    hh.disp_inc_bef_ret = sum([p.disp_inc_bef_ret for p in hh.sp])
    hh.debt_payments = sum([hh.debts[debt].payment for debt in hh.debts])
    hh.cons_bef_ret_real = real(hh.disp_inc_bef_ret - hh.debt_payments)


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

    hh_tax = taxes.file_household(hh, year, common, prices)
    hh.disp_inc_after_ret = nom(hh_tax.fam_disp_inc)
    taxes.get_gis_oas(hh, hh_tax, year, prices)

    hh.debt_payments = sum([hh.debts[debt].payment for debt in hh.debts])
    hh.cons_after_ret_real = real(hh.disp_inc_after_ret - hh.debt_payments)
    hh.cons_after_ret_real -= getattr(hh, 'imputed_rent', 0)


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
        hh.d_output[f'{p.who}wage_{key}'] = real(p.d_wages[year])
        hh.d_output[f'{p.who}pension_{key}'] = real(p.pension)

    for residence in hh.residences:
        hh.d_output[f'{residence}_{key}'] = \
            real(hh.residences[residence].balance)
    if hasattr(hh, 'business'):
        hh.d_output[f'business_{key}'] = real(hh.business.balance)
    if 'first_mortgage' in hh.debts:
        hh.d_output[f'first_mortgage_balance_{key}'] = \
            real(hh.debts['first_mortgage'].balance)

    if key == 'bef':
        hh.d_output[f'disp_inc_{key}'] = real(hh.disp_inc_bef_ret)
        hh.d_output[f'cons_{key}'] = hh.cons_bef_ret_real

    if key in ['bef', 'part']:
        for p in hh.sp:
            if hasattr(p, 'rpp_dc'):
                hh.d_output[f'{p.who}rpp_dc_{key}'] = real(p.rpp_dc.balance)
            for acc in p.fin_assets:
                hh.d_output[f'{p.who}{acc}_balance_{key}'] = \
                    real(p.fin_assets[acc].balance)

    if key in ['bef', 'after']:
        hh.d_output[f'debt_payments_{key}'] = real(hh.debt_payments)

    if key in ['part', 'after']:
        for p in hh.sp:
            hh.d_output[f'{p.who}annuity_rrsp_{key}'] = p.annuity_rrsp_real
            hh.d_output[f'{p.who}annuity_rpp_dc_{key}'] = p.annuity_rpp_dc_real
            hh.d_output[f'{p.who}annuity_non_rrsp_{key}'] = \
                p.annuity_non_rrsp_real

    if key == 'after':
        hh.d_output[f'disp_inc_{key}'] = real(hh.disp_inc_after_ret)
        hh.d_output[f'cons_{key}'] = hh.cons_after_ret_real

        for p in hh.sp:
            hh.d_output[f'{p.who}years_to_retire'] = p.ret_age - p.init_age
            hh.d_output[f'{p.who}factor'] = p.factor
            hh.d_output[f'{p.who}cpp_{key}'] = real(p.cpp)
            hh.d_output[f'{p.who}gis_{key}'] = real(p.inc_gis)
            hh.d_output[f'{p.who}oas_{key}'] = real(p.inc_oas)
            if hasattr(p, 'rpp_db'):
                hh.d_output[f'{p.who}rpp_db_benefits_{key}'] = \
                    real(p.rpp_db.benefits)
