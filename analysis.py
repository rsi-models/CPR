import pandas as pd
import numpy as np

class Results:
    def __init__(self, input_data, output, common, prices, extra_params):
        self.input = input_data
        self.output = output
        self.common = common
        self.prices = prices
        self.extra_params = extra_params

    def summarize(self):
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
        Merges input with output and return combined dataframe and adds index
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
        Puts a consumption floor, computes RRI 
        (NaN if cons before and after retirement below cons_floor)
        and checks preparedness for retirement.
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