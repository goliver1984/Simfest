from setuptools import find_packages, setup


setup(
    name='simfest',
    version='1.0',
    description='Discord Bot for Simfest UK',
    author='prryplatypus',
    packages=find_packages(),
    install_requires=[
        'discord.py'
    ],
    extras_require={
        'dev': [
            'black',
        ]
    }
)
