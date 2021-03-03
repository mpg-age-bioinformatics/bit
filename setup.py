from setuptools import setup

setup(name = 'bit',
      version = '0.2.0',
      description = '[b]ermuda [i]nformation [t]riangle',
      url = 'https://github.com/mpg-age-bioinformatics/bit',
      author = 'Bioinformatics Core Facility of the Max Planck Institute for Biology of Ageing',
      author_email = 'bioinformatics@age.mpg.de',
      license = 'MIT',
      packages = [ 'bit' ],
      install_requires = [ "requests >= 2.0.1","six", "xlrd==1.2.0", "openpyxl==3.0.5"],
      zip_safe = False,
      entry_points = {'console_scripts': ['bit=bit.__init__:main','mail=bit.automation:main']}
      )
