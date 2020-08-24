import tools
import taxes
import simulator
import importlib
importlib.reload(taxes)
importlib.reload(simulator)


def compute_bs_bef_ret(hh, year, common, prices):
    """
    Computes pre-retirement consumption for household

    :type hh: object
    :param hh: Instance of the initialisation.Household class.

    :type common: object
    :param common: Instance of the macro.Common class

    :type t: integer
    :param t: Period identification.
    """
    nom_2016 = tools.create_nom_2016(year, prices)

    hh_tax = taxes.file_household(hh, year, common, prices)
    for who, sp in enumerate(hh.sp):
        sp.net_income_bef_ret = (sp.fin_assets['unreg'].net_withdrawal
                                 + nom_2016(common.tax.paftertax(hh_tax, who)))
    compute_cons_bef_ret(hh, year, prices)


def compute_cons_bef_ret(hh, year, prices):
    """
    Compute consumption before retirement

    :type hh: object
    :param hh: Instance of the initialisation.Household class.
    """
    real = tools.create_real(year, prices)

    hh.net_income_bef_ret = sum([sp.net_income_bef_ret for sp in hh.sp])
    hh.contributions = sum([sp.contributions_rrsp + sp.contributions_non_rrsp
                            for sp in hh.sp])
    hh.debt_payments = sum([hh.debts[debt].payment for debt in hh.debts])
    hh.cons_bef_ret_real = real(hh.net_income_bef_ret - hh.contributions
                              - hh.debt_payments)


def add_output(hh, year, prices, key):
    """
    Extracts balance sheet for key = before, partial, after retirement.
    """
    real = tools.create_real(year, prices)

    for sp in hh.sp:
        hh.d_output[f'{sp.who}wage_{key}'] = real(sp.d_wages[year])
        hh.d_output[f'{sp.who}pension_{key}'] = real(sp.pension)

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
        for sp in hh.sp:
            if hasattr(sp, 'rpp_dc'):
                hh.d_output[f'{sp.who}rpp_dc_{key}'] = real(sp.rpp_dc.balance)
            for acc in sp.fin_assets:
                hh.d_output[f'{sp.who}{acc}_balance_{key}'] = \
                    real(sp.fin_assets[acc].balance)

    if key in ['bef', 'after']:
        hh.d_output[f'debt_payments_{key}'] = real(hh.debt_payments)

    if key in ['part', 'after']:
        for sp in hh.sp:
            hh.d_output[f'{sp.who}annuity_rrsp_{key}'] = sp.annuity_rrsp_real
            hh.d_output[f'{sp.who}annuity_dc_{key}'] = sp.annuity_rpp_dc_real
            hh.d_output[f'{sp.who}annuity_tfsa_{key}'] = sp.annuity_tfsa_real
            hh.d_output[f'{sp.who}annuity_unreg_{key}'] = sp.annuity_unreg_real

    if key == 'after':
        hh.d_output[f'net_income_{key}'] = real(hh.net_income_after_ret)
        hh.d_output[f'cons_{key}'] = hh.cons_after_ret_real

        for sp in hh.sp:
            hh.d_output[f'{sp.who}years_to_retire'] = sp.ret_age - sp.init_age
            hh.d_output[f'{sp.who}factor'] = sp.factor
            hh.d_output[f'{sp.who}cpp_{key}'] = real(sp.cpp)
            hh.d_output[f'{sp.who}gis_{key}'] = real(sp.inc_gis)
            hh.d_output[f'{sp.who}oas_{key}'] = real(sp.inc_oas)
            if hasattr(sp, 'rpp_db'):
                hh.d_output[f'{sp.who}rpp_db_benefits_{key}'] = \
                    real(sp.rpp_db.benefits)


def compute_bs_after_ret(hh, year, common, prices):
    """
    Compute balance sheet after retirement.

    :type hh: object
    :param hh: Instance of the initialisation.Household class.

    :type common: object
    :param common: Instance of the macro.Common class

    :type t: integer
    :param t: Period identification.
    """
    nom, real = tools.create_nom_real(year, prices)
    nom_2016 = tools.create_nom_2016(year, prices)

    hh_tax = taxes.file_household(hh, year, common, prices)
    hh.net_income_after_ret = nom_2016(common.tax.haftertax(hh_tax))
    taxes.get_gis_oas(hh, hh_tax, year, prices)

    if hh.couple:
        hh_tax_split = taxes.file_household_split(hh, hh_tax, year, common,
                                                  prices)
        net_income_split = nom_2016(common.tax.haftertax(hh_tax_split))
        if net_income_split > hh.net_income_after_ret:
            hh.net_income_after_ret = net_income_split
            taxes.get_gis_oas(hh, hh_tax, year, prices)

    hh.debt_payments = sum([hh.debts[debt].payment for debt in hh.debts])
    hh.cons_after_ret_real = real(hh.net_income_after_ret - hh.debt_payments)
    if hasattr(hh, 'imputed_rent_real'):
        hh.cons_after_ret_real -= nom(hh.imputed_rent_real)
