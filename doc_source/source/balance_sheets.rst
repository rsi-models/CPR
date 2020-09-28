Balance Sheets
==============

This module holds functions that compute the various balance sheet items 
for each household at different points in the simulation process. 
A collection of variables are calculated and added to the output dataframe
retrieved by the module *main*.

At age 55 or in the year preceding retirement if the latter intervenes before
age 56, wages, pensions, consumption, accounts balances(rrsp, other registered, tfsa
and unregistered accounts, as well as DC RPPs) are calculated. 
They are stored in variables ending in '_bef'.

For couples who do not retire at the same time, wages, pensions, account balances
and annuities of the first spouse to retire are calculated.
They are stored in variables ending in '_part'.

At age 65 or in the year of retirement if the latter intervenes later, 
consumption, pension, annuities, DB RPP, CPP, OAS and GIS benefits, 
as well as the values of residences and outstanding mortgages 
are stored in variables ending in '_aft'.

In the case of couples, the variables describing the spouse who retires last
start with 's_'.

.. automodule:: CPR.balance_sheets
    :members: compute_bs_bef_ret, compute_cons_bef_ret, compute_bs_after_ret,
              add_output
