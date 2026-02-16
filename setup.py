"""
HYPHA SDK - P2P Infrastructure for Autonomous AI Agents
"""

from setuptools import setup, find_packages
import os

# Read README for long description
readme_path = os.path.join(os.path.dirname(__file__), "README.md")
with open(readme_path, "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
with open(requirements_path, "r") as fh:
    requirements = [
        line.strip()
        for line in fh
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="hypha-sdk",
    version="0.1.0",
    author="HYPHA Team",
    author_email="team@hypha.network",
    description="P2P Infrastructure for Autonomous AI Agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pointsnode/hypha-network",
    packages=find_packages(include=['hypha_sdk', 'hypha_sdk.*', 'src', 'src.*']),
    python_requires=">=3.8",
    install_requires=requirements,
    include_package_data=True,
    package_data={
        'src': ['discovery/*.js', 'messaging/*.js'],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="p2p, blockchain, ai-agents, autonomous-agents, web3, hyperswarm",
    project_urls={
        "Bug Reports": "https://github.com/Pointsnode/hypha-network/issues",
        "Source": "https://github.com/Pointsnode/hypha-network",
        "Documentation": "https://github.com/Pointsnode/hypha-network/tree/main/docs",
    },
)
