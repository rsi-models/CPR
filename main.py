import importlib
from functools import partial
import numpy as np
import multiprocessing as mp
import time
import pandas as pd
import initialisation
import macro
import simulator
import tools
import analysis
importlib.reload(initialisation)
importlib.reload(macro)
importlib.reload(simulator)
importlib.reload(tools)
importlib.reload(analysis)


def run_simulations(inputs, nsim=1, non_stochastic=False, **extra_params):
    """
    This function launches the simulations.
    """
    start = time.time()
    # check extra_params in common_params or prices:
    l_params = []
    for file_csv in ['prices.csv', 'common_params.csv', 'user_options.csv']:
        pars = tools.get_params('../data/pars/' + file_csv)
        l_params.extend(pars.keys())
    for par in extra_params:
        assert par in l_params, f'{par} is not a parameter'

    if non_stochastic:
        nsim = 1

    common = macro.CommonParameters(nsim, non_stochastic, extra_params)
    prices = macro.Prices(common, extra_params)

    d_input = inputs.to_dict('index')
    l_outputs = []
    start = time.time()

    hhs = [initialisation.create_hh(index, d_hh, common, prices)
           for index, d_hh in d_input.items()]
    jobs = [(hh, sim) for hh in hhs for sim in range(nsim)]

    if common.multiprocessing:
        with mp.Pool(processes=mp.cpu_count()) as pool:
            l_outputs = pool.map(partial(simulator.simulate,
                                 common=common, prices=prices), jobs)
    else:
        l_outputs = [simulator.simulate(job, common, prices) for job in jobs]


    output = pd.DataFrame.from_dict(l_outputs)
    print(f'total time: {time.time() -  start}')
    results = analysis.Results(inputs, output, common, prices,
                                   extra_params)

    return results
