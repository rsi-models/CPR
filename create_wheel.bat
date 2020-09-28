:: change version

del /q /s dist CRP.egg-info
python setup.py sdist bdist_wheel 

twine check dist/*
twine upload --repository-url https://test.pypi.org/legacy/ -u rsi -p ire.hec.ca1u!! --verbose dist/* 

:: twine upload --repository pypi dist/* --verbose