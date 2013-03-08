from distutils.core import setup

setup(
    name='GifTiffLoader',
    version='0.1.4',
    author='David N. Mashburn',
    author_email='david.n.mashburn@gmail.com',
    packages=['GifTiffLoader'],
    scripts=[],
    url='http://pypi.python.org/pypi/GifTiffLoader/',
    license='LICENSE.txt',
    description='automatically load multi-dimensional Tiff and Gif files and file sequences as numpy arrays using PIL',
    long_description=open('README.rst').read(),
    install_requires=[
         #'wxPython>=2.6', # wxPython isn't being found correctly by setuptools -- please install it manually!
         "numpy >= 0.9",
         "PIL >= 1.1.5",
         "FilenameSort >= 0.1.1"
    ],
)
