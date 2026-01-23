import re

from setuptools import find_packages, setup


def get_version():
    with open("pykrx/__init__.py", encoding="UTF-8") as f:
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', f.read())
        if match:
            return match.group(1)
    raise RuntimeError("Unable to find version string.")


with open("README.md", encoding="UTF-8") as fh:
    long_description = fh.read()

setup(
    name="pykrx",
    version=get_version(),
    description="KRX data scraping",
    url="https://github.com/sharebook-kr/pykrx/",
    author="Brayden Jo, Jonghun Yoo",
    author_email=(
        "brayden.jo@outlook.com, jonghun.yoo@outlook.com, pystock@outlook.com"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "requests",
        "pandas",
        "datetime",
        "numpy",
        "xlrd",
        "deprecated",
        "multipledispatch",
        "matplotlib",
    ],
    license="MIT",
    packages=find_packages(include=["pykrx", "pykrx.*", "pykrx.stock.*"]),
    package_data={
        "pykrx": ["*.ttf"],
    },
    python_requires=">=3",
    zip_safe=False,
)
