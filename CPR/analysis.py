import os
import pandas as pd
import numpy as np


module_dir = os.path.dirname(os.path.dirname(__file__))


def get_dataset():
    """
    Function that returns a dataframe of synthetic data.

    Returns
    -------
    pandas.core.frame.DataFrame
        Dataframe of synthetic data.
    """
    return pd.read_csv(module_dir + '/CPR/data/inputs/synth_inputs.csv',
                       index_col=0)


class Results:
    """
    This class prepares the results.

    Parameters
    ----------
    input_data: pandas.core.frame.DataFrame
        dataframe of inputs
    output: pandas.core.frame.DataFrame
        dataframe of outputs
    common: Common
        instance of the class Common
    prices: Prices
        instance of the class Prices
    extra_params: dict
        dictionary of extra parameters
    """
    def __init__(self, input_data, output, common, prices, extra_params):
        self.input = input_data
        self.output = output
        self.common = common
        self.prices = prices
        self.extra_params = extra_params

    def summarize(self):
        """
        Function to summarize the simulation.
        """
        if self.common.non_stochastic is True:
            print('\nDeterministic Model')
        else:
            print(f'\nStochastic Model, {self.common.nsim} simulations')

        if self.extra_params != {}:
            print('\nExtra parameters:')
            for k, v in self.extra_params.items():
                print(f'{k}: {v}')


    def merge(self, add_index=True):
        """
        Function to merge input and output variables to create a database.

        Parameters
        ----------
        add_index : bool, optional
            add index to database, True by default
        """
        self.df_merged = self.input.merge(self.output, how='left',
                                          left_index=True, right_on='hh_index')
        if add_index:
            if self.common.nsim == 1:
                self.df_merged.set_index('hh_index', inplace=True)
            else:
                self.df_merged.set_index(['hh_index', 'sim'], inplace=True)


    def check_preparedness(self, factor_couple=2, cons_floor=100,
                           d_cutoffs={20: 80, 100: 65}):
        """
        Function that introduces a consumption floor, computes RRI (NaN if consumption before and after retirement below cons_floor), and checks preparedness for retirement.

        Parameters
        ----------
        factor_couple : int, optional
            factor to normalize income for couple, by default 2
        cons_floor : int, optional
            consumption floor, by default 100
        d_cutoffs : dict, optional
            cutoffs, by default {20: 80, 100: 65}
        """
        if not hasattr(self, 'df_merged'):
            self.merge()

        # adjusts consumption
        self.df_merged[['cons_bef', 'cons_after']] = \
            self.df_merged[['cons_bef', 'cons_after']].clip(lower=cons_floor)
        # compute RRI
        self.df_merged['rri'] = \
            self.df_merged.cons_after / self.df_merged.cons_bef * 100
        mask = ((self.df_merged.cons_bef == cons_floor) &
                (self.df_merged.cons_after == cons_floor))
        self.df_merged.loc[mask, 'rri'] = np.nan

        # compute cutoffs
        def compute_hh_wage(row):
            """
            Function to compute a normalized wage for the household.

            Parameters
            ----------
            row : pandas.core.series.Series
                row of pandas.core.frame.DataFrame

            Returns
            -------
            float
                Normalized wage.
            """
            if row['couple']:
                return (row['init_wage'] + row['s_init_wage']) / factor_couple
            return row['init_wage']

        self.df_merged['hh_init_adj_wage'] = \
            self.df_merged.apply(compute_hh_wage, axis=1)

        l_quantiles = [k/100 for k in d_cutoffs.keys()][:-1]
        l_cutoffs = self.df_merged.hh_init_adj_wage.quantile(l_quantiles)
        d_cutoffs_by_cat = {i: v for i, (k, v) in enumerate(d_cutoffs.items())}

        # apply cutoffs to households inital wages
        self.df_merged['category'] = \
            np.searchsorted(l_cutoffs, self.df_merged.hh_init_adj_wage)
        self.df_merged['rri_cutoff'] = \
            self.df_merged.category.replace(d_cutoffs_by_cat)
        self.df_merged.drop(columns='category', inplace=True)
        self.df_merged['prepared'] = \
            self.df_merged.rri >= self.df_merged.rri_cutoff
