:: change version

del /q /s dist build cpr_rsi.egg-info
python setup.py sdist bdist_wheel 

twine check dist/*
twine upload --repository pypi -u rsi -p ire.hec.ca1u!! --verbose dist/*

:: to test: twine upload --repository-url https://test.pypi.org/legacy/ -u rsi -p ire.hec.ca1u!! --verbose dist/* 