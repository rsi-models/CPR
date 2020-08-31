import importlib
import sys
import numpy as np
sys.path.insert(1, 'C:/Users/pyann/Dropbox (CEDIA)/srd/Model')
import srd
import tools


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
    hh_tax = file_household_amount_to_tax(hh, year, common, prices)
    hh_tax_0 = file_household(hh, year, common, prices)
    
    for who, p in enumerate(hh.sp):
        p.fin_assets['unreg'].amount_after_tax_real = (
            common.tax.paftertax(hh_tax, who)
            - common.tax.paftertax(hh_tax_0, who))
        p.fin_assets['unreg'].compute_after_tax_inc()
        p.fin_assets['unreg'].compute_net_withdrawal(common)


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
    real_2018 = tools.create_real(year, prices)

    p_tax = []  # persons in household (1 or 2)
    for p in hh.sp:
        p = srd.Person(othtax=real_2018(p.othtax), age=p.age,
                       earn=real_2018(p.earn), rpp=real_2018(p.rpp),
                       cpp=real_2018(p.cpp), othntax=real_2018(p.othntax),
                       con_rrsp=real_2018(p.con_rrsp),
                       inc_rrsp=real_2018(p.inc_rrsp),
                       div_other_can=p.div_other_can))
        p_tax.append(p)

    if hh.couple:
        hh_tax = srd.Hhold(p_tax[0], p_tax[1], prov=hh.prov)
    else:
        hh_tax = srd.Hhold(p_tax[0], prov=hh.prov)
    common.tax.compute(hh_tax)
    return hh_tax

def file_household_amount_to_tax(hh, year, common, prices):
    """
    Files household with taxable income and cap gains from withdrawals
    from unreg assets.

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
    real_2018 = tools.create_real(year, prices)

    p_tax = []  # persons in household (1 or 2)
    for p in hh.sp:
        p = srd.Person(
            othtax=real_2018(p.othtax + p.fin_assets['unreg'].amount_to_tax),
            age=sp.age, earn=real_2018(p.earn), rpp=real_2018(p.rpp),
            cpp=real_2018(p.cpp), othntax=real_2018(p.othntax),
            con_rrsp=real_2018(p.con_rrsp), inc_rrsp=real_2018(p.inc_rrsp),
            div_other_can=p.div_other_can)
        p_tax.append(p)

    if hh.couple:
        hh_tax = srd.Hhold(p_tax[0], second=p_tax[1], prov=hh.prov)
    else:
        hh_tax = srd.Hhold(p_tax[0], prov=hh.prov)
    common.tax.file(hh_tax)
    return hh_tax


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
