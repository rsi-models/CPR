# Import packages

# %matplotlib inline
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import sys
#sys.path.insert(1, r'C:/Users/roger/Documents/GitHub/CPR/CPR')
sys.path.insert(1, '/Users/TessaLoRiggio/CEDIA Dropbox/Tessa LoRiggio/RSI/CPR/CPR')
#os.path.normpath(os.getcwd() + os.sep + os.pardir)
#sys.path.insert(1, '../CPR')


import analysis
import main

pd.options.display.max_columns = None
pd.options.display.max_rows = None

#nj = (os.getcwd()=='C:\\Users\\80002036\\CEDIA Dropbox\\Nicholas-James Clavet\\Modeles\\srd\\notebooks')

#if nj :
#    sys.path.append('C:/Users/80002036/Documents/GitHub/srd')
#    sys.path.append('C:/Users/80002036/Documents/GitHub/srpp')
#    print('Utilisateur : NJ')

#if not nj:
#    sys.path.append('C:/Users/roger/Documents/GitHub/srd')
#    sys.path.append('C:/Users/roger/Documents/GitHub/srpp')
#    print('Utilisateur : Roger')

"""# Import dataset"""

#from CPR import analysis
#import analysis

#inputs = analysis.get_dataset()
#inputs = (pd.read_csv('C:/Users/roger/Documents/GitHub/CPR/CPR_out/CPR/data/inputs/synth_inputs.csv',index_col=0))[:25]
#inputs = (pd.read_csv('C:/Users/roger/Documents/GitHub/CPR/CPR_out/inputs.csv',index_col=0))[332:333]
#inputs = pd.read_csv('C:/Users/roger/Documents/GitHub/CPR/CPR/Notebooks/my_inputs.csv',index_col=0)

#inputs = pd.read_csv('C:/Users/roger/Documents/GitHub/CPR/CPR_out/my_inputs.csv',index_col=0)
inputs = pd.read_csv('./my_inputs.csv',index_col=0)

inputs.head(2)

"""# Run model
Deterministic model and stochastic model with 25 simulations
"""

#from CPR import main
#import main

res_deter = main.run_simulations(inputs, 1, non_stochastic=True)
res_deter.summarize()

res_stoch = main.run_simulations(inputs, 25, non_stochastic=False)
res_stoch.summarize()

"""# Analyse results

## See output
"""

res_deter.output.head()

#stop

"""## Merge with input and check preparedness"""

res_deter.check_preparedness()
df = res_deter.df_merged

print(f'percentage people prepared in sample: {df.prepared.mean() * 100}%')

"""## RRI distribution"""

sns.set()
ax = df.rri[df.rri < 500].hist()
ax.set_title('RRI distribution')
plt.show()

"""## Risk
### Preparation rate at aggregate level
"""

res_stoch.check_preparedness()
df = res_stoch.df_merged

ax = df.groupby('sim')['prepared'].mean().hist()
ax.grid()
ax.set_title('rri distribution')
ax.set_xlabel('percentage people prepared')
ax.grid()
plt.show()

"""## Experiments

### Selling first residence
"""

vars(res_deter.common)

res_not_selling = main.run_simulations(inputs, 1, non_stochastic=True,
                                       sell_first_resid=False)
res_not_selling.summarize()
res_not_selling.check_preparedness()
df = res_not_selling.df_merged

print(f'\npercentage people prepared without selling house: {df.prepared.mean() * 100:.2f}%')

res_selling = main.run_simulations(inputs, 1, non_stochastic=True,
                                   sell_first_resid=True)
res_selling.summarize()
res_selling.check_preparedness()
df = res_selling.df_merged

print(f'\npercentage people prepared when selling house: {df.prepared.mean() * 100:.2f}%')

vars(res_deter.prices)

mu_equity_bm = res_deter.prices.mu_equity
mu_bills_bm = res_deter.prices.mu_bills
mu_bonds_bm = res_deter.prices.mu_bonds

factors = np.linspace(0, 2, 10)

l_prepared = []
for factor in factors:
    res = main.run_simulations(inputs, 1, non_stochastic=True,
                               mu_equity=factor * mu_equity_bm,
                               mu_bills=factor * mu_bills_bm,
                               mu_bonds=factor * mu_bonds_bm)
    res.check_preparedness()
    l_prepared.append(res.df_merged.prepared.mean())

plt.plot(factors, l_prepared)
plt.title('changes in returns')
plt.xlabel('factor')
plt.ylabel('percentage prepared')
plt.show()

"""# Using CPR with other inputs

More info on the variables here: http://ire.hec.ca/en/wp-content/uploads/sites/3/2020/06/cpr-report-2020-final.pdf
"""

inputs.head()

# saving copy of dataframe
inputs.iloc[0, :].to_frame().T.to_csv('my_inputs.csv', index=False)

my_inputs = pd.read_csv('my_inputs.csv')

my_res = main.run_simulations(my_inputs, 100, non_stochastic=False)
my_res.check_preparedness()
df = my_res.df_merged

df.prepared.value_counts(normalize=True)

ax = sns.distplot(df.loc[df.rri<500, 'rri'])
ax.grid()
ax.set_title('rri distribution')
ax.grid()
plt.show()