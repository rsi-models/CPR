import pandas as pd
import numpy as np
#import matplotlib.pyplot as plt
#import seaborn as sns

#import CPR
#from CPR import analysis, main
import sys
import os 
os.path.normpath(os.getcwd() + os.sep + os.pardir)
sys.path.insert(1, '../CPR')
import analysis
import main
import macro

#Création d'une personne type (comme dans le simulateur) pour identifier les variations lors de changements sur les variables pertinentes
cpr = analysis.get_dataset() 
d_hh = {var: np.nan for var in cpr.columns}
d_vars = {'byear': 1980,
          'sex': 'male',
          'ret_age': 65,
          'claim_age_cpp': 65,
          'education': 'less than high school',
          'init_wage': 60000,
          'weight': 1,
          'couple': False,
          'prov': 'qc',
          'mix_bills': 0,
          'mix_bonds': 0.4,
          'mix_equity': 0.6,
          'fee': 0.015,
          'fee_equity': 0.015,
          'cap_gains_unreg': 0,
          'realized_losses_unreg': 0,
          'init_room_rrsp': 60000,
          'init_room_tfsa': 60000,
          "first_mortgage": 100000,
          'first_residence': 200000,
          'first_mortgage_payment': 1000}
d_hh.update(d_vars)

#Test de la simulation pour vérifier que les résultats sont identiques à ceux sur l'application web
results = main.run_simulations(pd.Series(d_hh), n_jobs=1, sell_first_resid=True, downsize=0.3, mu_price_rent=15, mu_housing = 0.0161, non_stochastic=True, base_year=2020, ret_equity_2018 = 0.0313, ret_bills_2018 = -0.0193, ret_bonds_2018 = -0.0129, ret_housing_2018 = 0.1062, ret_business_2018 = 0.0313)
print(results.output.transpose())
