call sphinx-build -b latex ./source build/latex/en
call sphinx-build -b latex ./source build/latex/fr
call sphinx-build -b html ./source build/html/en -D language='en' 
call sphinx-build -b html ./source build/html/fr -D language='fr'

xcopy "build/html" /s "../docs" /y