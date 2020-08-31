import importlib
import taxes
import tools
importlib.reload(taxes)
importlib.reload(tools)


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


def liquidate_fin_assets(p):
    """
    Liquidate financial assets.

    Parameters
    ----------
    p : Person
        spouse in household 
    """
    for acc in ['rrsp', 'rpp_dc', 'tfsa', 'unreg']:
        setattr(p, f'val_annuities_{acc}', 0)
    for acc in p.fin_assets:
        if acc in ['rrsp', 'other_reg']:
            p.val_annuities_rrsp += p.fin_assets[acc].liquidate()
        elif acc == 'tfsa':
            p.val_annuities_tfsa += p.fin_assets[acc].liquidate()
        else:
            p.val_annuities_unreg += p.fin_assets[acc].liquidate()
    if hasattr(p, 'rpp_dc'):
        p.val_annuities_rpp_dc += p.rpp_dc.liquidate()


def compute_factors(hh, p, rate, prices):
    """
    Compute individual factor for annuities constant in real terms. We use an 
    adjusted rate to smooth excess factor volatility. This is because
    we take the total return on bonds in the year that the annuity
    is purchased. The whole interest structure should be used and mean reversion
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
    adj_rate = rate_real - prices.adj_fact_annuities * (rate_real - prices.mu_bonds)
    p.factor = prices.d_factors[sp.sex][hh.prov].ann(
        p.byear, agestart=sp.age, rate=adj_rate)
    real_rate_zero_ret = 1 / (1 + prices.inflation_rate) - 1
    p.factor_0 = prices.d_factors[sp.sex][hh.prov].ann(
        p.byear, agestart=sp.age, rate=-real_rate_zero_ret)


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

    p.annuity_rrsp_real += real(p.val_annuities_rrsp / p.factor)
    p.annuity_rpp_dc_real += real(p.val_annuities_rpp_dc / p.factor)
    p.annuity_tfsa_real += real(p.val_annuities_tfsa / p.factor)
    p.annuity_tfsa_0_real += real(p.val_annuities_tfsa / p.factor_0)
    p.annuity_unreg_real += real(p.val_annuities_unreg / p.factor)
    p.annuity_unreg_0_real += real(p.val_annuities_unreg / p.factor_0)

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

def liquidate_real_assets(hh, year, common, prices):
    """
    Liquidate real assets (housing and business).

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
    float
        liquidation value
    float
        realized capital gains
    """
    value_liquidation, cap_gains_liquidation = 0, 0

    if common.sell_first_resid & ('first_residence' in hh.residences):
        impute_real_rent(hh, year, prices)
        hh.residences['first_residence'].liquidate()
        value_liquidation += hh.residences['first_residence'].sell_value
        if 'first_mortgage' in hh.debts:
            value_liquidation -= hh.debts['first_mortgage'].balance
            hh.debts['first_mortgage'].balance = 0

    if common.sell_second_resid & ('second_residence' in hh.residences):
        hh.residences['second_residence'].liquidate()
        value_liquidation += hh.residences['second_residence'].sell_value
        cap_gains_liquidation += hh.residences['second_residence'].cap_gains
        if 'second_mortgage' in hh.debts:
            value_liquidation -= hh.debts['second_mortgage'].balance
            hh.debts['second_mortgage'].balance = 0

    if common.sell_business & hasattr(hh, 'business'):
        hh.business.liquidate(common)
        value_liquidation += hh.business.selling_price
        cap_gains_liquidation += hh.business.cap_gains

    return value_liquidation, cap_gains_liquidation

def impute_real_rent(hh, year, prices):
    """
    Compute imputed rent.

    Parameters
    ----------
    hh: Hhold
        household
    year : int
        year
    prices : Prices
        instance of the class Prices
    """
    hh.imputed_rent_real = (hh.residences['first_residence'].balance
        / prices.d_price_rent_ratio[year] / prices.d_infl_factors[year])
