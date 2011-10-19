from distutils.core import setup

setup(
    name='ScholarScrape',
    version='0.1.0',
    packages=['scholar',
                'scholar.scholar',
                'scholar.spiders',
                'scholar.pipelines',
                'scholar.extensions',
             ],
    license='GNU GENERAL PUBLIC LICENSE 3',
    long_description=open('README.rst').read(),
    author = 'Patrick Browne',
    author_email = 'pt.browne@gmail.com',
    url = 'http://www.google.fr'
)
