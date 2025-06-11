"""
Setup script for ElfAutomations package
"""

from setuptools import find_packages, setup

setup(
    name="elf-automations",
    version="0.1.0",
    description="Autonomous AI Company Platform",
    author="ElfAutomations",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
