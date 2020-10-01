Macro
=====

The Macro module contains classes that contain parameters common to all households, 
generate stochastic processes for returns and wages and other prices.

.. currentmodule:: CPR.macro

.. autoclass:: CommonParameters
    :members: set_limits, prepare_ympe, prepare_cpp

.. autoclass:: Prices
    :members: simulate_ret, compute_params_process, simulate_housing,
              prepare_inflation_factors, simulate_interest_debt,
              attach_diff_log_wages, initialize_factors
