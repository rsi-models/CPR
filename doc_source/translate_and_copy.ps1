<# https://www.sphinx-doc.org/en/master/usage/advanced/intl.html #>

sphinx-build -b html ./source build/html/en -D language='en'
sphinx-build -b html ./source build/html/fr -D language='fr'