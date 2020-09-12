import sys
from CPR import tools
sys.path.insert(1, 'C:/Users/pyann/Dropbox (CEDIA)/srd/Model')
import srd


def compute_after_tax_amount(hh, year, common, prices):
    """
    Compute net nominal return and net amount from withdrawal
    for unregistered assets.

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
    hh_srd = file_household_inc_to_tax(hh, year, common, prices)
    hh_srd_0 = file_household(hh, year, common, prices)

    for who, p in enumerate(hh.sp):
        if p.liquidation_to_tax:
            p.liquidation_after_tax = nom(
                hh_srd.sp[who].disp_inc - hh_srd_0.sp[who].disp_inc)
        else:
            p.fin_assets['unreg'].amount_after_tax = nom(
                hh_srd.sp[who].disp_inc - hh_srd_0.sp[who].disp_inc)


def file_household(hh, year, common, prices):
    """
    Files household using SRD.

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

    Returns
    -------
    Hhold
        instance of class Hhold after tax
    """
    real = tools.create_real(year, prices)

    hh_srd = []  # persons in household (1 or 2)
    for p in hh.sp:
        p_srd = srd.Person(age=p.age, earn=real(p.earn), rpp=real(p.rpp),
                           cpp=real(p.cpp),
                           net_cap_gains=real(p.net_cap_gains),
                           prev_cap_losses=real(p.prev_cap_losses),
                           div_elig=real(p.div_elig),
                           div_other_can=real(p.div_other_can),
                           othtax=real(p.other_taxable),
                           othntax=real(p.other_non_taxable),
                           inc_rrsp=real(p.inc_rrsp),
                           con_rrsp=real(p.con_rrsp),
                           con_non_rrsp=real(p.con_non_rrsp),
                           asset=real(p.assets))
        hh_srd.append(p_srd)

    if hh.couple:
        hh_srd = srd.Hhold(hh_srd[0], second=hh_srd[1], prov=hh.prov)
    else:
        hh_srd = srd.Hhold(hh_srd[0], prov=hh.prov)
    common.tax.compute(hh_srd)

    return hh_srd


def file_household_inc_to_tax(hh, year, common, prices):
    """
    Files household with taxable income (interests and dividends)
    from unregistered assets.

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

    Returns
    -------
    Hhold
        instance of class Hhold after tax
    """
    real = tools.create_real(year, prices)

    hh_srd = []  # persons in household (1 or 2)
    for p in hh.sp:
        inc_div_elig = common.share_div_elig * p.fin_assets['unreg'].inc_div
        inc_int_other_div = (p.fin_assets['unreg'].inc_int
                             + p.fin_assets['unreg'].inc_div - inc_div_elig)

        non_taxable = p.liquidation_non_taxable
        cap_gains = p.liquidation_cap_gains
        cap_losses = common.frac_cap_gains * p.liquidation_cap_losses
        business_exempt = p.liquidation_business_exempt

        p_srd = srd.Person(age=p.age, earn=real(p.earn), rpp=real(p.rpp),
                           cpp=real(p.cpp),
                           net_cap_gains=real(p.net_cap_gains + cap_gains),
                           prev_cap_losses=real(p.prev_cap_losses
                                                + cap_losses),
                           cap_gains_exempt=real(business_exempt),
                           div_elig=real(p.div_elig + inc_div_elig),
                           div_other_can=real(p.div_other_can),
                           othtax=real(p.other_taxable + inc_int_other_div),
                           othntax=real(p.other_non_taxable + non_taxable),
                           inc_rrsp=real(p.inc_rrsp),
                           con_rrsp=real(p.con_rrsp),
                           con_non_rrsp=real(p.con_non_rrsp),
                           asset=real(p.assets))
        hh_srd.append(p_srd)

    if hh.couple:
        hh_srd = srd.Hhold(hh_srd[0], second=hh_srd[1], prov=hh.prov)
    else:
        hh_srd = srd.Hhold(hh_srd[0], prov=hh.prov)
    common.tax.compute(hh_srd)
    return hh_srd


def get_gis_oas(hh, hh_tax, year, prices):
    """
    Computes nominal GIS and OAS benefits

    Parameters
    ----------
    hh: Hhold
        household
    hh_tax : Hhold
        household
    year : int
        year
    prices : Prices
        instance of the class Prices
    """
    nom_2018 = tools.create_nom(year, prices)

    for who, p in enumerate(hh.sp):
        p.inc_gis = nom_2018(hh_tax.sp[who].inc_gis)
        p.inc_oas = nom_2018(hh_tax.sp[who].inc_oas)
