from CPR import tools
from CPR import taxes
from CPR import simulator


def compute_bs_bef_ret(hh, year, common, prices):
    """
    Function to compute the pre-retirement balance sheet.

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
    Function to compute pre-retirement consumption.

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
    Function to compute the post-retirement balance sheet.

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
    for inc in ['fam_inc_tot', 'fam_after_tax_inc', 'fam_disp_inc']:
        val = nom(getattr(hh_tax, inc))
        setattr(hh, f'{inc}_after_ret', val)
    taxes.get_gis_oas_allowances(hh, hh_tax, year, prices)

    hh.debt_payments = sum([hh.debts[debt].payment for debt in hh.debts])
    hh.cons_after_ret_real = real(hh.fam_disp_inc_after_ret - hh.debt_payments)
    hh.cons_after_ret_real -= real(getattr(hh, 'imputed_rent', 0))


def add_output(hh, year, prices, key):
    """
    Function to extract output variables.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    prices : Prices
        instance of the class Prices
    key : str
        before ("bef"), when first spouse retires ("part") 
        or after retirement ("aft")
    """
    real = tools.create_real(year, prices)

    for p in hh.sp:
        hh.d_output[f'{p.who}wage_{key}'] = real(p.d_wages[year])
        hh.d_output[f'{p.who}pension_{key}'] = real(p.pension)

    for residence in hh.residences:
        hh.d_output[f'{residence}_{key}'] = \
            real(hh.residences[residence].balance)    
    business = real(hh.business.balance) if hasattr(hh, 'business') else 0
    hh.d_output[f'business_{key}'] = business
        
    if 'first_mortgage' in hh.debts:
        hh.d_output[f'first_mortgage_balance_{key}'] = \
            real(hh.debts['first_mortgage'].balance)

    if key == 'bef':
        hh.d_output[f'year_cons_bef'] = hh.cons_bef_ret_year
        hh.d_output[f'cons_{key}'] = hh.cons_bef_ret_real

    if key in ['bef', 'part']:
        for p in hh.sp:
            rpp_dc = real(p.rpp_dc.balance) if hasattr(p, 'rpp_dc') else 0
            hh.d_output[f'{p.who}rpp_dc_{key}'] = rpp_dc
            for acc in p.fin_assets:
                hh.d_output[f'{p.who}{acc}_balance_{key}'] = \
                    real(p.fin_assets[acc].balance)

    if key in ['part', 'after']:
        for p in hh.sp:
            hh.d_output[f'{p.who}annuity_rrsp_{key}'] = p.annuity_rrsp_real
            hh.d_output[f'{p.who}annuity_rpp_dc_{key}'] = p.annuity_rpp_dc_real
            hh.d_output[f'{p.who}annuity_non_rrsp_{key}'] = \
                p.annuity_non_rrsp_real

    if key == 'after':
        hh.d_output[f'year_cons_after'] = hh.cons_after_ret_year
        hh.d_output[f'imputed_rent_{key}'] = real(getattr(hh, 'imputed_rent', 0))
        hh.d_output[f'cons_{key}'] = hh.cons_after_ret_real
        hh.d_output[f'debt_payments_{key}'] = real(hh.debt_payments)
        hh.d_output[f'fam_net_tax_liability_{key}'] = real(
            hh.fam_inc_tot_after_ret - hh.fam_after_tax_inc_after_ret)

        for p in hh.sp:
            hh.d_output[f'{p.who}cpp_{key}'] = real(p.cpp)
            hh.d_output[f'{p.who}gis_{key}'] = real(p.inc_gis)
            hh.d_output[f'{p.who}oas_{key}'] = real(p.inc_oas)
            hh.d_output[f'{p.who}allow_surv_{key}'] = real(p.allow_surv)
            hh.d_output[f'{p.who}allow_couple_{key}'] = real(p.allow_couple)          
            db_benefits = real(p.rpp_db.benefits) if hasattr(p, 'rpp_db') else 0
            hh.d_output[f'{p.who}rpp_db_benefits_{key}'] = db_benefits
            hh.d_output[f'{p.who}business_dividends_{key}'] = real(getattr(p, 'div_other_can', 0))