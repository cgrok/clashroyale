from setuptools import setup, find_packages

setup(
    name='clashroyale',
    packages=find_packages(),
    version=version,
    description='An (a)sync wrapper for royaleapi.com',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license='MIT',
    url='https://github.com/cgrok/clashroyale',
    keywords=['clashroyale', 'wrapper', 'cr', 'royaleapi'],
    include_package_data=True,
    install_requires=['aiohttp==3.3.2', 'python-box==3.1.1', 'requests==2.18.4'],
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
