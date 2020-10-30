<# https://www.sphinx-doc.org/en/master/usage/advanced/intl.html #>

<# pdf documentation #>
Get-ChildItem build\pdf| Remove-Item -Recurse
sphinx-build -M latexpdf ./source build/pdf/en -D language='en'
sphinx-build -M latexpdf ./source build/pdf/fr -D language='fr'


<# html documentation #>
Get-ChildItem build\html| Remove-Item -Recurse
sphinx-build -b html ./source build/html/en -D language='en'
sphinx-build -b html ./source build/html/fr -D language='fr'

<# delete everything in docs (except .nojekyll for github page) and copy html files #>
Get-ChildItem ..\docs -Exclude .nojekyll| Remove-Item -Recurse
Copy-Item -Path "build\html\*" -Destination "..\docs" -Recurse