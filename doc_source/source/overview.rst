****************************
Getting Started With the CPR
****************************

Installing the CPR
==================

The CPR can be easily installed using pip::

  pip install cpr-rsi

Please read the `terms of use <https://pypi.org/policy/terms-of-use/>`_ for *pypi*, the website hosting the package.

The CPR uses two other packages that are produced by the RSI and the Research Chair on Intergenerational Economics (CREEi), which is supported by the RSI: the Disposable Income Simulator (`Simulateur de revenu disponible, or SRD <https://creei-models.github.io/srd/>`_; documentation in French), which computes taxes and major benefits; and the Public Pension Plans Simulator (`Simulateur de régimes de pensions publiques, or SRPP <https://creei-models.github.io/srpp/>`_; documentation in French), which simulates QPP and CPP contributions and benefits. Both the SRD and the SRPP are automatically installed along with the CPR.

In a notebook or a project, the CPR is called by adding the following command:

.. code:: ipython3

    import CPR

To uninstall the CPR, the SRD and the SRPP, pip can be used::

  pip uninstall cpr-rsi srd srpp

Development/Alternative Install
===============================

If one is unable to use pip, or to install the CPR in order to modify it, retrieving it from Github is the first step::

  git clone https://github.com/rsi-models/CPR.git

Then it can be installed by going to cpr/ from the terminal and launching::

  pip install -e .

The changes made will directly impact the installed file.

Such a development install must be made within an environment (e.g. `conda environment <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html>`_) that includes *pandas* and *numpy*.

If one does not want the CPR anymore, the *cpr*, *srd* and *srpp* folders can simply be deleted.


For further details on how to use the CPR, please consult the :ref:`tutorial` section.

As mentioned elsewhere, note the CPR is provided "as is" under `an MIT license <https://rsi-models.github.io/CPR/credits.html#licence>`_.

If you have questions, comments or suggestions, do not hesitate to contact us (:ref:`nous_contacter`).
