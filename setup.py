# py_mssql/setup.py

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README.md for the long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read the requirements from requirements.txt
def read_requirements(filename):
    return [
        line.strip()
        for line in open(filename)
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="polars_mssql",  
    version="0.3.2",  
    author="Dave Rosenman",
    author_email="daverosenman@gmail.com",
    description="Effortlessly connect to SQL Server to import data into Polars DataFrames and export data back to SQL Server.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/drosenman/py_mssql",  
    license="MIT",  # Choose an appropriate license
    packages=find_packages(exclude=["tests", "docs"]),
    install_requires=read_requirements("requirements.txt"),
    python_requires=">=3.7",  
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  
        "Intended Audience :: Developers",
        "Topic :: Database",
    ],
    keywords="sql server polars sqlalchemy database",
    include_package_data=True,  
    project_urls={  # Optional
        "Bug Reports": "https://github.com/drosenman/py_mssql/issues",
        "Source": "https://github.com/drosenman/py_mssql",
    },
)
