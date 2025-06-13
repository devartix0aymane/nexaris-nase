from setuptools import setup, find_packages
import os

# Read the contents of README.md file
with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Read the requirements from requirements.txt file
with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as f:
    requirements = f.read().splitlines()

setup(
    name="nexaris-nase",
    version="0.1.0",
    author="NEXARIS - Aymane Loukhai (devartix0aymane)",
    author_email="info@nexaris.com",
    description="NEXARIS Adaptive Scenario Engine for cybersecurity training",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/devartix0aymane",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Security",
        "Topic :: Education :: Computer Aided Instruction (CAI)",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'nase=nase.cli:main',
        ],
    },
    include_package_data=True,
)