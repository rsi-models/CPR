import os
from functools import partial
import multiprocessing as mp
import pandas as pd

# remove 8 lines below and uncomment next 5 lines when CPR package is updated 
import sys 
#os.path.normpath(os.getcwd() + os.sep + os.pardir)
#sys.path.insert(1, '../CPR')
sys.path.append('/Users/TessaLoRiggio/CEDIA Dropbox/Tessa LoRiggio/RSI/CPR_master_mac2015')
import initialisation
import macro
import simulator
import tools
import analysis
#from CPR import initialisation
#from CPR import macro
#from CPR import simulator
#from CPR import tools
#from CPR import analysis

module_dir = os.path.dirname(os.path.dirname(__file__))
path = '/CPR/data/params/'

def run_simulations(inputs, nsim=1, non_stochastic=False, n_jobs=None,
                    **extra_params):
    """
    This function launches the simulations. Any parameter can be changed
    using extra_params.

    Parameters
    ----------
    inputs : _io.TextIOWrapper
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
    
    if type(inputs) is pd.Series:
        d_input = inputs.to_frame().to_dict()
    else:
        d_input = inputs.to_dict('index')

    hhs = [initialisation.create_hh(index, d_hh, common, prices)
           for index, d_hh in d_input.items()]
    jobs = [(hh, sim) for hh in hhs for sim in range(nsim)]

    if n_jobs is None:
            n_jobs = mp.cpu_count()
    
    if n_jobs > 1:
        with mp.Pool(processes=n_jobs) as pool:
            l_outputs = pool.map(partial(simulator.simulate,
                                 common=common, prices=prices), jobs)
    else:
        l_outputs = [simulator.simulate(job, common, prices) for job in jobs]

    output = pd.DataFrame.from_dict(l_outputs)
    results = analysis.Results(inputs, output, common, prices, extra_params)
    return results
