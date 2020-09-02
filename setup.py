import setuptools
import glob
with open("README.md", "r") as f:
	long_description = f.read()
setuptools.setup(
	name="pyutils",
	version="0.1",
	descripton="my util functions for python",
	long_description=long_description,
	long_description_content_type="text/markdown",
	packages=setuptools.find_packages(),
	license="MIT",
	author="SuperStormer",
	author_email="larry.p.xue@gmail.com",
	url="https://github.com/SuperStormer/pyutils",
	project_urls={"Source Code": "https://github.com/SuperStormer/pyutils"},
	scripts=glob.glob("scripts/*.py"),
	install_requires=["pycryptodome>=3.9.8", "cryptography>=2.9.2", "requests>=2.24.0"]
)