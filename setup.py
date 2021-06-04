from setuptools import setup

with open("README.md", "r") as file:
    long_des = file.read()

setup(
    name="pythonpixels",
    packages=["pythonpixels",],
    install_requires=["pillow","rich"],
    description="An API wrapper for the python discord pixels project",
    version="1.2.13",
    long_description=long_des,
    long_description_content_type="text/markdown",
    license="MIT",
    author="sebkuip",
    author_email="sebkuip@tekx.it",
    url="https://github.com/sebkuip/pythonpixels",
    keywords=["API"],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
    ]
)