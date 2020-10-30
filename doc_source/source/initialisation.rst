Initialisation
==============

This module sets up households and attaches assets and debts to them. The table below shows all the individual inputs to the CPR (some of them are entered in other modules).

.. image:: images/table_inputs.png

Though an example input file is provided as part of the package, a tutorial is also offered to show users how to modify those inputs to use the ones of their choice. NOTE: users must be careful when using their inputs, as a general error message will be generated if any of the -- numerous -- inputs is incorrectly specified (i.e. contains a mistake or is highly implausible).

.. currentmodule:: CPR.initialisation

.. autofunction:: create_hh

.. autoclass:: Person
    :members: create_wage_profile, create_shocks

.. autoclass:: Hhold
    :members: set_other_years
