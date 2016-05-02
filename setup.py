from distutils.core import setup

setup(name='tpapi',
      version='0.3',
      description="Small client library for interacting with Target Process Service",
      url='https://github.com/ash30/tpapi',
      author='Ashley Arthur',
      packages = ['tpapi'],
      install_requires = ['requests']
      )
