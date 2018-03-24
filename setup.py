from setuptools import setup

setup(
    name='clashroyale',
    packages=['clashroyale'],
    version='v3.2.0',
    description='An (a)sync wrapper for royaleapi.com',
    author='kyb3r',
    license='MIT',
    url='https://github.com/cgrok/clashroyale',
    keywords=['clashroyale', 'wrapper', 'cr', 'royaleapi'],
    install_requires=['aiohttp>=2.0.0,<2.3.0', 'python-box==3.1.1', 'requests==2.18.4', 'asynctest==0.12.0'],
)
