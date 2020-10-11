import glob

import setuptools

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
	install_requires=[
	"pycryptodome>=3.9.8", "requests>=2.24.0", "aiofiles>=0.5.0", "aiohttp>=3.6.2",
	"z3-solver>=4.8.9.0"
	]
)
