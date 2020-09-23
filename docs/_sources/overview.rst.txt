****************************
Getting Started With the CPR
****************************

Installing the CPR
==================

On peut installer facilement le SRD en utilisant pip::

  pip install srd

Le SRD dépend d'un autre package produit par la chaire, le SRPP, qui permet de simuler les revenus de pensions publiques (RPC et RRQ). Celui-ci est installé automatiquement en installant le SRD.

Dans un notebook ou un projet, on invoque le SRD en ajoutant la commande suivante:

.. code:: ipython3

    import srd

Pour désinstaller le SRD et le SRPP, il suffit d'utiliser pip::

  pip uninstall srd srpp

Si l'utilisation de pip n'est pas possible :

1. Allez sur `pypi.org <https://www.pypi.org>`_ et téléchargez les fichiers sources (extension .tar.gz) du SRD et du SRPP

2. Extrayez les fichiers .tar.gz. Sous Windows, ouvrez les fichiers avec 7-zip ou Winzip ou, dans une fenêtre de commande, entrez (en remplaçant les adresses et noms de fichiers)::

    tar -xvzf C:\\SENTIER_VERS_FICHIER\\FICHIER.tar.gz -C C:\\SENTIER_VERS_RÉPERTOIRE_EXTRACTION

3. Dans les dossiers qu’on vient d’extraire, *srd-x.x.x* et *srpp-x.x.x* (*x.x.x* étant le numéro de version), on trouve les répertoires *srd* et *srpp*

4. Placez *srd* et *srpp* dans le répertoire de votre choix

Pour invoquer le SRD, il faut ajouter son adresse:

.. code:: ipython3

    import sys
    sys.path.append("C:\SENTIER VERS RÉPERTOIRE_CONTENANT_SRD_ET_SRPP")

    import srd

Si l'on ne veut plus le SRD, il suffit d'effacer les répertoires *srd* et *srpp*.

En cas de questions, commentaires ou suggestions, n'hésitez pas à nous contacter: :ref:`nous_contacter`.



PLACEHOLDER FOR THE INPUT EXAMPLE DOCUMENT
