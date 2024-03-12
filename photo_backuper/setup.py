from setuptools import setup, find_packages

setup(
    name='photo_backuper',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # list any dependencies your package has
        "send2trash>=1.8.0",
    ],
)