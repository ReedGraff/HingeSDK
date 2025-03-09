from setuptools import setup, find_packages

setup(
    name="hingesdk",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.0",
        "pydantic>=1.8.0",
    ],
    author="Reed Graff",
    author_email="rangergraff@gmail.com",
    description="A Python SDK for the Hinge API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/reedgraff/hingesdk",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
