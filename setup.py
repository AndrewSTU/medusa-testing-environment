from setuptools import setup
from setuptools.command.install import install


class MyInstall(install):
    def run(self):
        install.run(self)
        try:
            from mte.main import main
            main()
        except ImportError:
            pass


setup(
    name="mte",
    version="3.0",
    description="Testing environment for Medusa security system",
    author='Roderik Ploszek',
    author_email='roderik.ploszek@gmail.com',
    license='MIT',
    packages = ['mte'],
    python_requires='>=3.11.2',
    install_requires=['paramiko==3.1.0', 'virtualbox==2.1.1', 'GitPython==3.1.31', 'PyYAML==5.4.1'],
    zip_safe=True,
    include_package_data=True,
    cmdclass={'install': MyInstall}
)