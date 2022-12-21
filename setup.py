from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in credit_limit_control/__init__.py
from credit_limit_control import __version__ as version

setup(
	name="credit_limit_control",
	version=version,
	description="to limit the credit",
	author="avientek",
	author_email="avientek.frappe",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
