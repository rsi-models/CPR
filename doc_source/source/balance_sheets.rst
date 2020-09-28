Balance Sheets
==============

This module holds functions that compute the various balance sheet items 
for each household at different points in the simulation process.

The following quantities are calculated and added to the output dataframe
produced by the module *main*:

* wage before retirement
* pension before retirement
* disposable income before and after retirement


'hh_index',
 'sim',
 's_wage_bef',
 's_pension_bef',
 'wage_bef',
 'pension_bef',
 'disp_inc_bef',
 'cons_bef',
 's_rpp_dc_bef',
 's_unreg_balance_bef',
 's_tfsa_balance_bef',
 'unreg_balance_bef',
 'rrsp_balance_bef',
 'tfsa_balance_bef',
 'debt_payments_bef',
 's_wage_part',
 's_pension_part',
 'wage_part',
 'pension_part',
 's_rpp_dc_part',
 's_unreg_balance_part',
 's_tfsa_balance_part',
 'unreg_balance_part',
 'rrsp_balance_part',
 'tfsa_balance_part',
 's_annuity_rrsp_part',
 's_annuity_rpp_dc_part',
 's_annuity_non_rrsp_part',
 'annuity_rrsp_part',
 'annuity_rpp_dc_part',
 'annuity_non_rrsp_part',
 's_wage_after',
 's_pension_after',
 'wage_after',
 'pension_after',
 'debt_payments_after',
 's_annuity_rrsp_after',
 's_annuity_rpp_dc_after',
 's_annuity_non_rrsp_after',
 'annuity_rrsp_after',
 'annuity_rpp_dc_after',
 'annuity_non_rrsp_after',
 'disp_inc_after',
 'cons_after',
 's_years_to_retire',
 's_factor',
 's_cpp_after',
 's_gis_after',
 's_oas_after',
 'years_to_retire',
 'factor',
 'cpp_after',
 'gis_after',
 'oas_after',
 'first_residence_bef',
 'first_mortgage_balance_bef',
 'first_residence_after',
 'first_mortgage_balance_after',
 'first_residence_part',
 'first_mortgage_balance_part',
 'rpp_dc_bef',
 'other_reg_balance_bef',
 'rpp_db_benefits_after',
 's_rrsp_balance_bef',
 'rpp_dc_part',
 'other_reg_balance_part',
 's_rrsp_balance_part',
 's_rpp_db_benefits_after',
 's_other_reg_balance_bef',
 's_other_reg_balance_part',
 'business_bef',
 'business_part',
 'business_after',
 'second_residence_bef',
 'second_residence_part',
 'second_residence_after']

.. automodule:: CPR.balance_sheets
    :members: compute_bs_bef_ret, compute_cons_bef_ret, compute_bs_after_ret,
              add_output
