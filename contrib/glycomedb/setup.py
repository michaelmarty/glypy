from setuptools import setup, find_packages

setup(
    name='glypy-glycomedb',
    version='0.0.5',
    packages=find_packages(),
    namespace_packages=["glypy", "glypy.io", "glypy.algorithms"]
)
