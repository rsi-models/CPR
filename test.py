import importlib
import numpy as np
import pandas as pd
import main
importlib.reload(main)
import time


df = pd.read_csv('CPR/data/inputs/inputs.csv', index_col=0)
inputs = df.loc[:, :]

sim_num = 1

if __name__ == '__main__':
    results = main.run_simulations(inputs, sim_num, non_stochastic=True,
                                   multiprocessing=False)
    results.check_preparedness(factor_couple=np.sqrt(2))
    results.summarize()

    prepared = results.df_merged.prepared
    weight = results.df_merged.weight
    print(np.average(prepared, weights= weight))
