.. CPR documentation master file, created by
   sphinx-quickstart on Tue Sep 15 15:41:15 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Canadians' Preparation for Retirement (CPR)
===========================================

The Canadians' Preparation for Retirement (CPR) tool was developed by a team at HEC Montréal's `Retirement and Savings Institute (RSI) <https://ire.hec.ca>`_, with financial support from the National Pension Hub at the `Global Risk Institute (GRI) <https://globalriskinstitute.org>`_. For any given household or group of households, it allows to compute retirement preparation using a number of hypotheses and processes, as well as a pre-set binary criterion defined in terms of the % of pre-retirement consumption -- income net of all taxes and contributions, including savings -- that households will likely be able to enjoy once they retire. As in past reports published in the 2010s, the default criterion is set at 65% of pre-retirement consumption for the top 4 income quintiles, and at 80% for the bottom income quintile.

Compared to other available tools, the CPR offers complete flexibility and transparency, in that its code is fully and freely available online and it can be modified and adapted at will. Importantly and distinctively, the CPR also allows to perform stochastic simulations, letting several dimensions vary over time according to cutting-edge processes and assumptions. All those can be modified by the sophisticated user, as can the number of replications that the tool uses to average outcomes and determine retirement preparation (or the probability thereof).


The CPR and the other tools it uses (SRD and SRPP) are written in Python, a modern, simple and fast language. In order to use it, it is essential to ensure first that an up-to-date Python distribution is installed, for example using Anaconda. Although not essential, it will also be useful to have a minimal understanding of Python environments and, if possible, vocabulary (e.g. function, class, instance, profile).


Le Simulateur de revenu disponible (SRD) a été mis au point par l’équipe de la Chaire de recherche sur les enjeux économiques intergénérationnels, une chaire conjointe HEC Montréal-ESG UQAM. Il permet, pour tout ménage, de calculer le revenu disponible ainsi que les impôts payés, les déductions, les crédits d’impôts et les principaux transferts obtenus, autant au fédéral qu’au provincial, pour les années 2016 à 2020 (le Québec et l’Ontario sont modélisés pour le moment; il est possible d’utiliser aisément l’une de ces deux structures fiscales pour toute autre province). Pour l’année 2020, les principales mesures d’urgence liées à la COVID-19 ont également été intégrées: PCU, PCUE, PIRTE, majorations du crédit de TPS/TVH et de l’Allocation canadienne pour enfants.

Par rapport aux autres outils existants, le SRD offre une très grande flexibilité et une transparence inégalée. En effet, tout ménage – quelles que soient sa composition et ses caractéristiques socio-économiques – peut être simulé dans le SRD, ce qui permet à l’utilisateur de simuler la base de données de son choix. De plus, le code du simulateur est public et modifiable, ce qui permet d’évaluer les effets de différents scénarios et de modifier les valeurs des paramètres et la structure du simulateur.

Le SRD est écrit en langage Python, un langage simple, rapide et moderne. Afin de pouvoir l’utiliser, il faut s’assurer d’avoir au préalable installé une distribution à jour de Python, par exemple à l’aide d”Anaconda. Bien que ce ne soit pas essentiel pour utiliser le SRD, il sera également utile de se familiariser un minimum, au préalable, avec le fonctionnement des environnements Python et avec le vocabulaire utilisé dans la présente documentation (p.ex. fonction, classe, instance, profil).



.. toctree::
   :maxdepth: 2
   :caption: Contents:

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
   tools.rst
   credits.rst



Index
=====

* :ref:`genindex`
