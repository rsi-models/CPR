****************************
Getting Started With the CPR
****************************

The CPR and the other tools it uses (SRD and SRPP) are written in Python, a modern, simple and fast language. In order to use it, it is essential to ensure first that an up-to-date Python distribution is installed, for example using Anaconda. In all cases, the minimum requirements to use the CPR are Python 3.6+ with *numpy*, *pandas* and *xlrd*. Although not essential, it will also be useful to have a minimal understanding of Python environments and, if possible, vocabulary (e.g. function, class, instance, profile).

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

Alternative Install
===================

If one is unable to install the CPR, a zip file containing CPR and its dependencies, SRD and SRPP, can be downloaded from `Github <https://github.com/rsi-models/CPR/releases>`_ (choose the file CPR_with_dep.zip in the latest release). To start using  the CPR, it suffices to unzip the file in the directory of your choice and either work from that directory or add the directory to the path (for example by using the module *sys*). A jupyter notebook explaining how CPR works, *Tutorial CPR*, is also included in the zip file.
If one does not want the CPR anymore, the *cpr*, *srd* and *srpp* folders can simply be deleted.

For further details on how to use the CPR, please consult the :ref:`tutorials <tutorial>`.

As mentioned elsewhere, note the CPR is provided "as is" under :ref:`an MIT licence <licence>`.

If you have questions, comments or suggestions, do not hesitate to :ref:`contact us <nous_contacter>`.
