import pathlib
import setuptools

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setuptools.setup(
    name="cpr-rsi",
    version="0.0.1",
    description="Assessing Canadians' Preparation for Retirement",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://rsi-models.github.io/CPR/",
    author="Team RSI",
    author_email="pyanni@gmail.com",
    license="MIT",
    classifiers=["Programming Language :: Python :: 3",
                 "License :: OSI Approved :: MIT License",
                 "Operating System :: OS Independent"],
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=["pandas", "numpy", "srpp", "srd"],
    python_requires=">=3.6")