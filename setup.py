import setuptools
with open("README.md", "r") as f:
	long_description = f.read()
setuptools.setup(
	name="miscutil",
	version="0.6",
	descripton="my util functions for python",
	long_description=long_description,
	long_description_content_type="text/markdown",
	packages=setuptools.find_packages(),
	license="GPLv3",
	author="SuperStormer",
	author_email="larry.p.xue@gmail.com",
	url="https://github.com/SuperStormer/miscutil",
	project_urls={"Source Code": "https://github.com/SuperStormer/miscutil"}
)