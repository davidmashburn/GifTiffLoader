from distutils.core import setup

setup(
    name='GifTiffloader',
    version='0.1',
    author='David N. Mashburn',
    author_email='david.n.mashburn@gmail.com',
    packages=['GifTiffloader'],
    scripts=[],
    url='http://pypi.python.org/pypi/GifTiffloader/',
    license='LICENSE.txt',
    description='',
    long_description=open('README.txt').read(),
    install_requires=[
         "numpy >= 0.9",
         "PIL >= 1.1.5",
    ],
)
