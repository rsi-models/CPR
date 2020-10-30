.. CPR documentation master file, created by
   sphinx-quickstart on Tue Sep 15 15:41:15 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Canadians' Preparation for Retirement (CPR)
===========================================

The Canadians' Preparation for Retirement (CPR) tool was developed by a team at HEC Montréal's `Retirement and Savings Institute (RSI) <https://ire.hec.ca/en>`_, with financial support from the National Pension Hub at the `Global Risk Institute (GRI) <https://globalriskinstitute.org>`_. It allows to compute retirement preparation for any household or group of households for which the user has the required input (personal and financial information) at any given point in time. It has been used with 2018 proprietary data to prepare `a report published by in June 2020 <https://ire.hec.ca/en/canadians-preparation-retirement-cpr/>`_.

As mentioned elsewhere, the CPR is provided "as is" under :ref:`an MIT licence <licence>`.

The CPR simulates the years between the base year and retirement, then converts all financial wealth into actuarially fair annuities upon retirement and compares post- and pre-retirement situations. Compared to other available tools, the CPR offers complete flexibility and transparency, in that its code is fully and freely available online and it can be modified and adapted at will. Importantly and distinctively, the CPR also allows to perform stochastic simulations, letting several dimensions vary over time according to cutting-edge processes and assumptions. All those can be modified by the sophisticated user, as can the number of replications that the tool uses to average outcomes and determine retirement preparation (or the probability thereof). The current version of the CPR takes 2018 as base year and the tax systems of Quebec and Ontario are currently modelled (other provinces can be approximated using one of these 2 provinces, preferably Ontario).

The CPR outputs a level of “consumption replacement” for each household that passes through the simulator and classifies each household as “prepared” or “unprepared”, according to the pre-set criterion. As in reports published by other groups in the 2010s, retirement preparation can be assessed by computing the ratio of post-retirement consumption to pre-retirement consumption and comparing it to a cutoff set at 65% for the top 4 income quintiles, and at 80% for the bottom income quintile. These measures can then be aggregated over all households analyzed to obtain a) the average of the replacement rate, or its distribution; and b) the proportion of households that are deemed “prepared”. When using the stochastic version of the tool, preparation probabilities can also be computed and visualized, for one or several households. The figure below  illustrates conceptually the parts and flows of the CPR.

The CPR and the other tools it uses (SRD and SRPP) are written in Python, a modern, simple and fast language. In order to use it, it is essential to ensure first that an up-to-date Python distribution is installed, for example using Anaconda. Although not essential, it will also be useful to have a minimal understanding of Python environments and, if possible, vocabulary (e.g. function, class, instance, profile).

.. image:: images/CPR_flow.png

.. toctree::
   :hidden:
   :maxdepth: 1

   VERSION FRANÇAISE <https://rsi-models.github.io/CPR/fr>
   ENGLISH VERSION <https://rsi-models.github.io/CPR/en>

   overview.rst
   main.rst
   simulator.rst
   initialisation.rst
   macro.rst
   assets.rst
   debts.rst
   taxes.rst
   annuities.rst
   life.rst
   balance_sheets.rst
   analysis.rst
   tools.rst
   tutorial.rst
   credits.rst


PDF Documentation
=================

Documentation :download:`pdf <../build/pdf/en/latex/cpr.pdf>`