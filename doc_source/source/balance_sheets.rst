Balance Sheets
==============

This module holds functions that compute the various balance sheet items for each household at different points in the simulation process. A collection of variables are calculated in real terms (base year 2018) and added to the output dataframe retrieved by the module *main*.

At age 55 or in the year preceding retirement, if the latter occurs before age 56, wages, consumption, earlier pensions, account balances (RRSP, other registered, TFSA and unregistered accounts, as well as DC RPPs) are calculated. They are stored in variables ending with '_bef'.

At age 65 or in the year of retirement, if the latter occurs later, consumption; earlier pensions; annuities purchased with financial assets (balances); DB RPP, CPP/QPP, and OAS/GIS/Allowances benefits; as well as the values of residences and outstanding mortgages, are stored in variables ending with '_aft'.

For couples who do not retire at the same time, wages, earlier pensions, account balances and annuities of the first spouse to retire are calculated. They are stored in variables ending with '_part'. Variables describing the spouse who retires last begin with 's\_'.

.. automodule:: CPR.balance_sheets
    :members: compute_bs_bef_ret, compute_cons_bef_ret, compute_bs_after_ret,
              add_output
