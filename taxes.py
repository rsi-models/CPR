import importlib
import numpy as np
from simtax import simtax
importlib.reload(simtax)
import tools
importlib.reload(simtax)


def compute_after_tax_amount(hh, year, common, prices):
    """
    Computes net nominal return of unreg assets (withdrawal not included)

    :type hh: object
    :param hh: Instance of the initialisation.Household class.

    :type common: object
    :param common: Instance of the macro.Common class.
    """
    hh_tax = file_household_amount_to_tax(hh, year, common, prices)
    hh_tax_0 = file_household(hh, year, common, prices)
    
    for who, sp in enumerate(hh.sp):
        sp.fin_assets['unreg'].amount_after_tax_real = (
            common.tax.paftertax(hh_tax, who)
            - common.tax.paftertax(hh_tax_0, who))
        sp.fin_assets['unreg'].compute_after_tax_inc()
        sp.fin_assets['unreg'].compute_net_withdrawal(common)


def file_household(hh, year, common, prices):
    """
    Files household.
    """
    real_2016 = tools.create_real_2016(year, prices)

    p_tax = []  # persons in household (1 or 2)
    for sp in hh.sp:
        p = simtax.person(othtax=real_2016(sp.othtax), age=sp.age,
                          earn=real_2016(sp.earn), rpp=real_2016(sp.rpp),
                          cpp=real_2016(sp.cpp), othntax=real_2016(sp.othntax),
                          con_rrsp=real_2016(sp.con_rrsp),
                          inc_rrsp=real_2016(sp.inc_rrsp),
                          cqppc=real_2016(sp.cpp_contrib))
        p_tax.append(p)

    if hh.couple:
        hh_tax = simtax.hhold(p_tax[0], second=p_tax[1], prov=hh.prov)
    else:
        hh_tax = simtax.hhold(p_tax[0], prov=hh.prov)
    common.tax.file(hh_tax)
    return hh_tax

def file_household_split(hh, hh_tax, year, common, prices):
    """
    Files household splitting taxable pensions.
    """
    # compute net transfers from 0 to 1
    income = []
    for sp in hh_tax.sp:
        income.append(sp.inc_oas + sp.inc_cpp + sp.inc_rpp + sp.inc_othtax)
    transfer = np.clip((income[0] - income[1]) / 2,
        -common.max_split * (hh_tax.sp[1].inc_rpp + hh_tax.sp[1].inc_othtax),
        common.max_split * (hh_tax.sp[0].inc_rpp + hh_tax.sp[0].inc_othtax))

    who = 0 if transfer > 0 else 1
    inc_rpp_othtax = hh_tax.sp[who].inc_rpp + hh_tax.sp[who].inc_othtax + 1e-12
    rpp_transfer = hh_tax.sp[who].inc_rpp / inc_rpp_othtax * transfer
    othtax_transfer = hh_tax.sp[who].inc_othtax / inc_rpp_othtax * transfer

    real_2016 = tools.create_real_2016(year, prices)
    p_tax = []  # persons in household (1 or 2)
    for who, sp in enumerate(hh.sp):
        if who == 0:
            rpp = real_2016(sp.rpp) - rpp_transfer
            othtax =real_2016(sp.othtax) - othtax_transfer
        else:
            rpp = real_2016(sp.rpp) + rpp_transfer
            othtax =real_2016(sp.othtax) + othtax_transfer

        p = simtax.person(
            rpp=rpp, othtax=othtax, age=sp.age, earn=real_2016(sp.earn),
            cpp=real_2016(sp.cpp), othntax=real_2016(sp.othntax),
            con_rrsp=real_2016(sp.con_rrsp), inc_rrsp=real_2016(sp.inc_rrsp),
            cqppc=real_2016(sp.cpp_contrib))
        p_tax.append(p)

    hh_tax = simtax.hhold(p_tax[0], second=p_tax[1], prov=hh.prov)
    common.tax.file(hh_tax)
    return hh_tax

def file_household_amount_to_tax(hh, year, common, prices):
    """
    Files household with taxable income and cap gains from withdrawals
    from unreg assets.
    """
    real_2016 = tools.create_real_2016(year, prices)

    p_tax = []  # persons in household (1 or 2)
    for sp in hh.sp:
        p = simtax.person(
            othtax=real_2016(sp.othtax + sp.fin_assets['unreg'].amount_to_tax),
            age=sp.age, earn=real_2016(sp.earn), rpp=real_2016(sp.rpp),
            cpp=real_2016(sp.cpp), othntax=real_2016(sp.othntax),
            con_rrsp=real_2016(sp.con_rrsp), inc_rrsp=real_2016(sp.inc_rrsp),
            cqppc=real_2016(sp.cpp_contrib))
        p_tax.append(p)

    if hh.couple:
        hh_tax = simtax.hhold(p_tax[0], second=p_tax[1], prov=hh.prov)
    else:
        hh_tax = simtax.hhold(p_tax[0], prov=hh.prov)
    common.tax.file(hh_tax)
    return hh_tax


def get_gis_oas(hh, hh_tax, year, prices):
    """
    Computes nominal GIS and OAS
    """
    nom_2016 = tools.create_nom_2016(year, prices)

    for who, sp in enumerate(hh.sp):
        sp.inc_gis = nom_2016(hh_tax.sp[who].inc_gis)
        sp.inc_oas = nom_2016(hh_tax.sp[who].inc_oas)
