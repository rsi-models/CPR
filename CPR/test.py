import sys
sys.path.insert(1, r'C:\Users\pyann\Dropbox (CEDIA)\CPR\Model')
import os
import numpy as np
import pandas as pd
from CPR import main

module_dir = os.path.dirname(os.path.dirname(__file__))
df = pd.read_csv(module_dir + '/inputs/inputs.csv', index_col=0)
inputs = df.sample(50)

sim_num = 25

if __name__ == '__main__':
    results = main.run_simulations(inputs, sim_num, non_stochastic=True,
                                   sell_first_resid=True,
                                   sell_second_resid=True,
                                   sell_business=True,
                                   multiprocessing=True)
    results.check_preparedness(factor_couple=np.sqrt(2))
    results.summarize()

    prepared = results.df_merged.prepared
    weight = results.df_merged.weight
    print(np.average(prepared, weights=weight))
