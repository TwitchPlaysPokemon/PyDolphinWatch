
from setuptools import setup
setup(
    name="dolphinWatch",
    version="0.1",
    packages=["dolphinWatch"],
    install_requires=['gevent>=1.1'],

    author="Felk",
    description="Python implementation of the DolphinWatch protocol, a socket based protocol to communicate with the dolphin emulator.",
    url="https://github.com/TwitchPlaysPokemon/PyDolphinWatch",
)
