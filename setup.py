
from setuptools import setup, find_packages
setup(
    name="dolphinWatch",
    version="0.2",
    packages=find_packages(),
    install_requires=['gevent>=1.1'],

    author="Felk",
    description="Python implementation of the DolphinWatch protocol, a socket based protocol to communicate with the dolphin emulator.",
    url="https://github.com/TwitchPlaysPokemon/PyDolphinWatch",
)
