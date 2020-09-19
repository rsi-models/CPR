from CPR import taxes
from CPR import tools


def compute_partial_annuities(hh, d_returns, year, prices):
    """
    Partially convert assets into annuities when first spouse retires.

    Parameters
    ----------
    hh: Hhold
        household
    d_returns : dict
        dictionary of returns
    year : int
        year
    prices : Prices
        instance of the class Prices
    """
    liquidate_fin_assets(hh.sp[0])
    for acc in ['rrsp', 'rpp_dc', 'tfsa', 'unreg']:
        setattr(hh.sp[1], f'val_annuities_{acc}', 0)
    compute_factors(hh, hh.sp[0], d_returns['bonds'][year], prices)
    convert_to_real_annuities(hh.sp[0], year, prices)
    hh.sp[0].retired = True


def compute_annuities(hh, d_returns, year, prices):
    """
    Fully convert assets into annuities when last spouse retires.

    Parameters
    ----------
    hh: Hhold
        household
    d_returns : dict
        dictionary of returns
    year : int
        year
    prices : Prices
        instance of the class Prices
    """
    for p in hh.sp:
        liquidate_fin_assets(p)
        compute_factors(hh, p, d_returns['bonds'][year], prices)
        convert_to_real_annuities(p, year, prices)
        p.retired = True


def liquidate_fin_assets(p):
    """
    Liquidate financial assets.

    Parameters
    ----------
    p : Person
        spouse in household
    """
    for acc in ['rrsp', 'rpp_dc', 'tfsa']:
        setattr(p, f'val_annuities_{acc}', 0)
    for acc in p.fin_assets:
        if acc in ['rrsp', 'other_reg']:
            p.val_annuities_rrsp += p.fin_assets[acc].liquidate()
        if acc == 'tfsa':
            p.val_annuities_tfsa += p.fin_assets[acc].liquidate()
    if hasattr(p, 'rpp_dc'):
        p.val_annuities_rpp_dc += p.rpp_dc.liquidate()


def compute_factors(hh, p, rate, prices):
    """
    Compute individual factor for annuities constant in real terms. We use an
    adjusted rate to smooth excess factor volatility. This is because
    we take the total return on bonds in the year that the annuity
    is purchased.
    The whole interest structure should be used and mean reversion
    would smooth out annuity prices.

    Parameters
    ----------
    hh: Hhold
        household
    p : Person
        spouse in household
    rate : float
        interest rate
    prices : Prices
        instance of the class Prices
    """
    rate_real = (1 + rate) / (1 + prices.inflation_rate) - 1
    adj_rate = (
        rate_real - prices.adj_fact_annuities * (rate_real - prices.mu_bonds))
    p.factor = prices.d_factors[p.sex][hh.prov].compute_annuity_factor(
        p.byear, agestart=p.ret_age, rate=adj_rate)
    real_rate_zero_ret = 1 / (1 + prices.inflation_rate) - 1
    p.factor_0 = prices.d_factors[p.sex][hh.prov].compute_annuity_factor(
        p.byear, agestart=p.ret_age, rate=-real_rate_zero_ret)


def convert_to_real_annuities(p, year, prices):
    """
    Converts assets to annuities in real terms.

    Parameters
    ----------
    p : Person
        spouse in household
    year : int
        year
    prices : Prices
        instance of the class Prices
    """
    real = tools.create_real(year, prices)

    if hasattr(p, 'liquidation_after_tax'):
        amount, p.liquidation_after_tax = p.liquidation_after_tax, 0
    else:
        amount = 0

    p.annuity_rrsp_real += real(p.val_annuities_rrsp) / p.factor
    p.annuity_rpp_dc_real += real(p.val_annuities_rpp_dc) / p.factor
    p.annuity_non_rrsp_real += real((p.val_annuities_tfsa + amount) / p.factor)
    p.annuity_non_rrsp_0_real += real((p.val_annuities_tfsa + amount)
                                      / p.factor_0)
