from distutils.core import setup

setup(
    name='GifTiffLoader',
    version='0.1',
    author='David N. Mashburn',
    author_email='david.n.mashburn@gmail.com',
    packages=['GifTiffLoader'],
    scripts=[],
    url='http://pypi.python.org/pypi/GifTiffLoader/',
    license='LICENSE.txt',
    description='',
    long_description=open('README.rst').read(),
    install_requires=[
         "numpy >= 0.9",
         "PIL >= 1.1.5",
    ],
)
