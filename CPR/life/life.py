import pandas as pd
import numpy as np
import requests
from os import path


class table:
    """
    Class computing annuity factors by province, gender, age and birth year.
    """
    def __init__(self, prov='qc', scenario='M', gender='males', web=False):
        self.params = path.join(path.dirname(__file__), 'params')
        quotes = pd.read_excel(self.params+'/quotients.xlsx',
                               sheet_name='DTH_Tx_Scenario_' + scenario,
                               skiprows=3)
        provdict = {'nl': 10,
                    'pe': 11,
                    'ns': 12,
                    'nb': 13,
                    'qc': 24,
                    'on': 35,
                    'mb': 46,
                    'sk': 47,
                    'ab': 48,
                    'bc': 59,
                    'yu': 60,
                    'nt': 61,
                    'nu': 62}
        sexdict = {'males': 1, 'females': 2}
        quotes = quotes[(quotes.CGT == provdict[prov]) &
                        (quotes.Sexe == sexdict[gender])]
        quotes = quotes.drop(columns=[-1, '110+', 'CGT'])
        names = list(quotes.columns.values)
        names[0] = 'year'
        names[1] = 'gender'
        quotes.columns = names
        quotes[['year', 'temp']] = quotes['year'].str.split('-', n=1, 
                                                            expand=True)
        # quotes['year'], quotes['temp'] = quotes['year'].str.split('-', 1).str
        quotes = quotes.drop(columns=['temp', 'gender'])
        quotes.set_index('year')
        # transform quotients into rates
        for a in range(0, 110):
            quotes[a] = 2.0*quotes[a] / (2.0-quotes[a])
            quotes[a] = np.where(quotes[a] > 1.0, 1.0, quotes[a])
        quotes = quotes.set_index('year')
        quotes[110] = quotes[109]
        quotes.columns = [str(i) for i in range(0, 111)]
        self.prospect = quotes
        if web is False:
            self.pull_history(prov, gender)
        else:
            self.pull_history_web(prov, gender)
        self.splice()

    # north west territories given saskatchewan retrospective mortality
    # because too short history.
    # newfoundland and labrador given new brunswick for same reason
    def pull_history_web(self, prov='qc', gender='males'):
        """
        Get historical mortalilty tables by province and gender.

        Parameters
        ----------
        prov: str
            province
        gender: str
            gender
        """
        maprov = {'qc': 'que',
                  'on': 'ont',
                  'bc': 'bco',
                  'ab': 'alb',
                  'nl': 'nbr',
                  'pe': 'pei',
                  'ns': 'nsc',
                  'nb': 'nbr',
                  'mb': 'man',
                  'sk': 'sas',
                  'nt': 'sas',
                  'yu': 'yuk'}
        file = ('http://www.prdh.umontreal.ca/BDLC/data/' + maprov[prov]
                + '/Mx_1x1.txt')
        r = requests.get(file)
        list_r = r.content.decode().split("\n")
        names = list_r[2].split()
        list_r = list_r[3:]
        r = 0
        for line in list_r:
            list_r[r] = line.split()
            r += 1
        history = pd.DataFrame(data=list_r, index=None, columns=names)
        history.loc[history.Age == '110+', 'Age'] = '110'
        history.dropna(axis=0, inplace=True)
        history['Year'] = history['Year'].astype('int64')
        history['Age'] = history['Age'].astype('int64')
        names = names[2:]

        for n in names:
            history[n] = np.where(history[n] == '.', '1.0', history[n])
            history[n] = history[n].astype('float64')
        if (gender == 'males'):
            history = history[['Year', 'Age', 'Male']]
        else:
            history = history[['Year', 'Age', 'Female']]
        history.columns = ['year', 'age', 'mx']
        history = pd.pivot_table(history, index=['year'], columns=['age'],
                                 values=['mx'])
        history = history['mx']
        history.columns = [str(a) for a in range(0, 111)]
        for a in range(0, 111):
            history[str(a)] = np.where(history[str(a)] > 1.0, 1.0,
                                       history[str(a)])
        self.history = history
        self.history.index = [str(i) for i in range(1921, 2012)]
        self.history.to_excel(self.params + f'/{prov}_{gender}.xlsx')

    def pull_history(self, prov='qc', gender='males'):
        """
        Get historical mortalilty tables by province and gender.

        Parameters
        ----------
        prov: str
            province
        gender: str
            gender
        """
        self.history = pd.read_excel(self.params + f'/{prov}_{gender}.xlsx')
        self.history.index = [str(i) for i in range(1921, 2012)]

    def splice(self):
        """
        Add survival probabilities for 2012 and after.
        """
        self.history.loc['2012'] = self.history.loc['2011']
        self.tab = self.history.append(self.prospect, sort=True)

    def compute_annuity_factor(self, byear, agestart, rate):
        """
        Compute annuity factor.

        Parameters
        ----------
        byear : int
            birth year
        agestart : int
            age at which annuity starts
        rate : float
            interest rate

        Returns
        -------
        float
            annuity factor
        """
        yrstart = byear + agestart
        prob_surv = 1
        present_value = 1

        for i in range(1, 111 - agestart):
            if yrstart + i < 2063:
                prob_surv *= (1 - self.tab.loc[str(yrstart + i - 1),
                                               str(agestart + i - 1)])
            else:
                prob_surv *= (1 - self.tab.loc['2062', str(agestart + i - 1)])
            present_value += prob_surv / ((1 + rate)**i)
        return present_value
