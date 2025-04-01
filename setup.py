from setuptools import setup, find_packages

setup(
    name="bestdori_app",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'PyQt6',
        'requests',
        'cairosvg'
    ],
) 