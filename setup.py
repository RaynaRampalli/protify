
from setuptools import setup, find_packages

setup(
    name='protify',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'matplotlib',
        'scikit-learn',
        'lightkurve',
        'astropy',
        'PyAstronomy'
    ],
    author='Rayna Rampalli',
    description='Protify: Rotation period detection and vetting using TESS light curves.',
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'protify=protify.cli:main',
        ]
    },
)
