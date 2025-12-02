#!/usr/bin/env python3
"""
Simple setup script for ResSimPlotter package.

This script can be used as an alternative to Poetry for basic installation.
For full development setup, Poetry is still recommended.
"""

from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ressimplotter",
    version="0.1.0",
    author="Daniel Hamill",
    author_email="daniel.d.hamill@USACE.army.mil",
    description="A Python package for reservoir simulation plotting and visualization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Visualization",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "matplotlib>=3.5.0",
        "numpy>=1.20.0",
        "pandas>=1.3.0",
        "plotly>=5.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=4.0.0",
            "mypy>=0.950",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/danhamill/ressimplotter/issues",
        "Source": "https://github.com/danhamill/ressimplotter",
    },
)