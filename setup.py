from setuptools import setup


with open('mte/requirements.txt') as f:
    requirements = f.read().splitlines()

setup(
    name="mte",
    version="3.0",
    description="Testing environment for Medusa security system",
    author='Roderik Ploszek',
    author_email='roderik.ploszek@gmail.com',
    license='MIT',
    packages = ['mte', 'mte.tests', 'mte.target'],
    python_requires='>=3.11.2',
    install_requires=requirements,
    zip_safe=True,
    include_package_data=True
)