****************************
Getting Started With the CPR
****************************

Installing the CPR
==================

The CPR can be easily installed using pip::

  pip install cpr-rsi

The CPR uses two other packages that are produced by the Research Chair on Intergenerational Economics (CREEi), which is supported by the RSI: the Disposable Income Simulator (`Simulateur de revenu disponible, or SRD <https://creei-models.github.io/srd/>`_; documentation in French), which computes taxes and major benefits; and the Public Pensions Income Simulator (Simulateur de revenu de pensions publiques, or SRPP), which simulates QPP and CPP benefits. Both the SRD and the SRPP are automatically installed along with the CPR.

In a notebook or a project, the CPR is called on by adding the following command:

.. code:: ipython3

    import cpr

To uninstall the CPR, the SRD and the SRPP, pip can be used::

  pip uninstall cpr srd srpp


##### part to be modified ###########

Pour l'installer afin de le modifier, il faut d'abord aller le chercher sur Github:

  git clone https://github.com/creei-models/srpp


Ensuite on peut l'installer en allant dans srpp/ et en lançant au terminal:

  python setup.py install -e

Les modifications apportées affecteront directement le fichier installé. Il est fortement recommandé de procéder à l'installation de développement dans un environnement (p.ex. `conda environment <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_)

########### end of part #####################

If one does not want the CPR, the *cpr*, *srd* and *srpp* folders can simply be deleted.

For more details on how to use the CPR, please consult the :ref:`tutorial` section.

If you have questions, comments or suggestions, do not hesitate to contact us (:ref:`nous_contacter`).
