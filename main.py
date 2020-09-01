import os
from functools import partial
import multiprocessing as mp
import time
import pandas as pd
from CPR import initialisation
from CPR import macro
from CPR import simulator
from CPR import tools
from CPR import analysis

module_dir = os.path.dirname(os.path.dirname(__file__))
path = '/CPR/data/params/'

def run_simulations(inputs, nsim=1, non_stochastic=False, **extra_params):
    """
    This function launches the simulations.

    Parameters
    ----------
    file : _io.TextIOWrapper
        csv file
    nsim : int, optional
        number of simulations, by default 1
    non_stochastic : bool, optional
        deterministic prices and price-rent ratio, by default False

    Returns
    -------
    Results
        instance of the class Results
    """
    start = time.time()
    # check extra_params in common_params or prices:
    l_params = []
    for file_csv in ['prices.csv', 'common_params.csv', 'user_options.csv']:
        params = tools.get_params(module_dir + path + file_csv)
        l_params.extend(params.keys())
    for param in extra_params:
        assert param in l_params, f'{param} is not a parameter'

    if non_stochastic:
        nsim = 1

    common = macro.CommonParameters(nsim, non_stochastic, extra_params)
    prices = macro.Prices(common, extra_params)

    d_input = inputs.to_dict('index')

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
    results = analysis.Results(inputs, output, common, prices, extra_params)
    return results
