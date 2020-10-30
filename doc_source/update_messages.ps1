<# run this when there is a change in the .rst files; it creates new messages to be translated
source: https://www.sphinx-doc.org/en/master/usage/advanced/intl.html #>

<# create new .pot files in build/gettext from .rst files #>
.\make gettext

<# update message to be translated for french version (.po files) #>
sphinx-intl update -p build/gettext -l fr