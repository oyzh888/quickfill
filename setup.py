from setuptools import find_packages, setup

setup(
    name="quickfill",
    version="0.0.1",
    description="AI makes form filling easy",
    author="oyzh",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    install_requires=[
        # 'numpy',
    ],
    python_requires=">=3.5",
)
