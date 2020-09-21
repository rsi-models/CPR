:: change version

del /q /s dist CRP.egg-info
python setup.py sdist bdist_wheel 

twine check dist/*
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
:: rsi; ire.hec.ca1u!!

:: twine upload --repository pypi dist/* --verbose