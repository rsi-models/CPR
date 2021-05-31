<# run this when there is a change in the .rst files; it creates new messages to be translated
source: https://www.sphinx-doc.org/en/master/usage/advanced/intl.html #>

<# make sure that sphinx, sphinx-rtd-theme, and sphinx-intl are installed#>

<# create new .pot files in build/gettext from .rst files #>
.\make gettext

<# update message to be translated for french version (.po files) #>
sphinx-intl update -p build/gettext -l fr