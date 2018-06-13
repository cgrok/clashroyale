from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='clashroyale',
    packages=['clashroyale'],
    version='v3.4.2',
    description='An (a)sync wrapper for royaleapi.com',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license='MIT',
    url='https://github.com/cgrok/clashroyale',
    keywords=['clashroyale', 'wrapper', 'cr', 'royaleapi'],
    install_requires=['aiohttp>=2.0.0,<2.3.0', 'python-box==3.1.1', 'requests==2.18.4', 'asynctest==0.12.0', 'yarl<1.2'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Games/Entertainment :: Real Time Strategy',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    python_requires='>=3.5'
)
