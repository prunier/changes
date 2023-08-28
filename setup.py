from setuptools import setup, find_packages

setup(
    name='changes',
    version='1.0',
    packages=find_packages(),
    scripts=['changes.py'],  # List of script files to include
    entry_points={
        'console_scripts': [
            'changes=changes:main',  # Define entry point for the script
        ],
    },
    author='prunier
    author_email='toutpres@yahoo.fr',
    description='Description of your package',
    url='https://github.com/prunier/changes,
)