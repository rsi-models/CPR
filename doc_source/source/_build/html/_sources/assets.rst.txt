Assets
======

This module manages all assets using various classes and functions: pension plans, individual savings (registered and unregistered), housing, business assets. It uses the contributions and room used as inputs as well as returns generated in the Macro module, and it updates all asset-related variables as the simulation progresses. 

.. currentmodule:: CPR.assets

.. autoclass:: ContributionRoom
    :members: compute_contributions, update_rrsp_room, update_tfsa_room,
              adjust_db_contributions, adjust_dc_contributions,
              adjust_employees_contributions, adjust_rrsp_contributions,
              adjust_tfsa_contributions, adjust_rrif,
              adjust_unreg_contributions, reset

.. autoclass:: FinAsset
    :members: update, rate, rrif_withdrawal, liquidate, reset

.. autoclass:: UnregAsset
    :members: update, compute_income, rate, update_balance, prepare_withdrawal,
              adjust_income, adjust_cap_losses, adjust_final_balance,
              liquidate, reset

.. autoclass:: RppDC

.. autoclass:: RppDB
    :members: compute_benefits, adjust_for_penalty, compute_cpp_adjustment,
              reset

.. autoclass:: RealAsset
    :members: update, liquidate, reset, impute_rent

.. autoclass:: Business
    :members: update, liquidate, reset
