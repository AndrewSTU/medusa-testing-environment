from setuptools import setup
from setuptools.command.install import install

import platform
import os
import subprocess


def install_sdk():
    if platform.system() == "Windows":
        vbox_dest = os.environ.get("VBOX_INSTALL_PATH", None)
        if vbox_dest is None:
            print("Missing 'VBOX_INSTALL_PATH' in evn path variable. Please edit env variable.")

        setup_path = os.path.dirname(__file__)
        current_path = os.getcwd()

        try:
            os.chdir(os.path.join(setup_path, 'sdk', 'installer'))
            result = subprocess.run(['py', 'vboxapisetup.py', 'install'])
            os.chdir(current_path)

            if result.returncode != 0:
                raise RuntimeError(result.stderr)
        except RuntimeError as e:
            print(f"Virtual Box SK installation failed. Please run it manually(sdk/installer/vboxapisetup.py):\n{e}")


class MyInstall(install):
    def run(self):
        install.run(self)
        install_sdk()
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