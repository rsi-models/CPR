import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="CPR",
    version="0.0.1",
    description="Canadians' Preparation for Retirement",
    long_description=README,
    long_description_content_type="text/markdown",
    # url=to be added,
    author="RSI",
    author_email="pyanni@gmail.com,
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=["CPR"],
    include_package_data=True,
    install_requires=["sys", "os", "functools", "multiprocessing", "time",
                      "pickle", "heapq", "pandas","numpy"],
    entry_points={
        "console_scripts": [
            "realpython=reader.__main__:main",
        ]
    },
)