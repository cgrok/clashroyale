from setuptools import setup

setup(
    name='clashroyale',
    packages=['clashroyale'],  # this must be the same as the name above
    version='v3.0.0',
    description='An async wrapper for cr-api.com',
    author='kyb3r',
    license='MIT',
    url='https://github.com/cgrok/clashroyale',  # use the URL to the github repo
    keywords=['clashroyale'],  # arbitrary keywords
    classifiers=[],
    install_requires=['aiohttp>=2.0.0,<2.3.0'],
)
