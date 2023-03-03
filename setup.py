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
	scripts=glob.glob("scripts/*"),
	install_requires=[
	"pycryptodome>=3.15.0", "requests>=2.28.0", "aiofiles>=0.8.0", "aiohttp>=3.8.1",
	"z3-solver>=4.10.2.0", "keystone-engine>=0.9.2", "beautifulsoup4>=4.11.1", "lxml>=4.9.2"
	]
)
