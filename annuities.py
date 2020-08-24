import importlib
import taxes
import tools
importlib.reload(taxes)
importlib.reload(tools)


def compute_partial_annuities(hh, d_returns, year, prices):
    """
    Creates annuities with assets and rpp_dc
    """
    liquidate_fin_assets(hh.sp[0])
    for acc in ['rrsp', 'rpp_dc', 'tfsa', 'unreg']:
        setattr(hh.sp[1], f'val_annuities_{acc}', 0)
    compute_factors(hh, hh.sp[0], d_returns['bonds'][year], prices)
    convert_to_real_annuities(hh.sp[0], year, prices)
    hh.sp[0].retired = True


def liquidate_fin_assets(sp):
    for acc in ['rrsp', 'rpp_dc', 'tfsa', 'unreg']:
        setattr(sp, f'val_annuities_{acc}', 0)
    for acc in sp.fin_assets:
        if acc in ['rrsp', 'other_reg']:
            sp.val_annuities_rrsp += sp.fin_assets[acc].liquidate()
        elif acc == 'tfsa':
            sp.val_annuities_tfsa += sp.fin_assets[acc].liquidate()
        else:
            sp.val_annuities_unreg += sp.fin_assets[acc].liquidate()
    if hasattr(sp, 'rpp_dc'):
        sp.val_annuities_rpp_dc += sp.rpp_dc.liquidate()


def compute_factors(hh, sp, rate, prices):
    """
    Compute individual factor for annuities constant in real terms. We use an 
    adjusted rate to smooth excess factor volatility. The latter is due to the 
    fact that we take the total return on bonds in the year that the annuity
    is purchased. The whole interest structure should be used and mean reversion
    would smooth out annuity prices.
    """
    rate_real = (1 + rate) / (1 + prices.inflation_rate) - 1
    adj_rate = rate_real - prices.adj_fact_annuities*(rate_real-prices.mu_bonds)
    sp.factor = prices.d_factors[sp.sex][hh.prov].ann(
        sp.byear, agestart=sp.age, rate=adj_rate)
    real_rate_zero_ret = 1 / (1 + prices.inflation_rate) - 1
    sp.factor_0 = prices.d_factors[sp.sex][hh.prov].ann(
        sp.byear, agestart=sp.age, rate=-real_rate_zero_ret)


def convert_to_real_annuities(sp, year, prices):
    """
    Converts assets to annuities constant in real terms 
    (base year = 2018).
    """
    real = tools.create_real(year, prices)

    sp.annuity_rrsp_real += real(sp.val_annuities_rrsp / sp.factor)
    sp.annuity_rpp_dc_real += real(sp.val_annuities_rpp_dc / sp.factor)
    sp.annuity_tfsa_real += real(sp.val_annuities_tfsa / sp.factor)
    sp.annuity_tfsa_0_real += real(sp.val_annuities_tfsa / sp.factor_0)
    sp.annuity_unreg_real += real(sp.val_annuities_unreg / sp.factor)
    sp.annuity_unreg_0_real += real(sp.val_annuities_unreg / sp.factor_0)

def compute_annuities(hh, d_returns, year, prices):
    """
    Creates annuities with common assets and rpp_dc

    :type hh: object
    :param hh: Instance of the initialisation.Household class.

    :type common: object
    :param common: Instance of the macro.Common class

    :type prices: object
    :param prices: Object of the macro.Prices class

    :type t: integer
    :param t: Period identification.

    :type rate_annuities: float
    :param rate_annuities: Rate used for annuities

    :type partial: bool
    :param partial: True if partial retirement.
    """
    for sp in hh.sp:
        liquidate_fin_assets(sp)
        compute_factors(hh, sp, d_returns['bonds'][year], prices)
        convert_to_real_annuities(sp, year, prices)
        sp.retired = True

def liquidate_real_assets(hh, year, common, prices):
    """
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
    Imputes rent by dividing value of the house by price/rent ratio
    """
    hh.imputed_rent_real = (hh.residences['first_residence'].balance
        / prices.d_price_rent_ratio[year] / prices.d_infl_factors[year])
