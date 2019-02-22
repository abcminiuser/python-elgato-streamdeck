import setuptools

with open("README.md", 'r') as f:
    long_description = f.read()

setuptools.setup(
   name='streamdeck',
   version='0.2.1',
   description='Library to control Elgato StreamDeck devices.',
   author='Dean Camera',
   author_email='dean@fourwalledcubicle.com',
   url='https://github.com/abcminiuser/python-elgato-streamdeck',
   package_dir={'': 'src'},
   packages=setuptools.find_packages(where='src'),
   install_requires=[],
   license="MIT",
   long_description=long_description,
   long_description_content_type="text/markdown",
   include_package_data=True,
)
