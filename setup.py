from setuptools import setup, find_packages

requirements = [
    'requests',
]

setup(
    name='iZettle',
    packages=find_packages(include=['iZettle']),
    version='0.1.0',
    description='',
    author='Aleksi Wikman',
    author_email='aleksi@vilkas.fi',
    url='https://github.com/vilkasgroup/iZettle',
    license="MIT license",
    keywords=['izettle', 'POS', 'Payment'],
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
    ],
)
