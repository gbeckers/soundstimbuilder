import sys
import versioneer
import setuptools

if sys.version_info < (3,6):
    print("Soundstimbuilder requires Python 3.6 or higher please upgrade")
    sys.exit(1)

long_description = \
"""A package to create experimental sound stimuli.

"""

setuptools.setup(
    name='soundstimbuilder',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=['soundstimbuilder', 'soundstimbuilder.praattextgrids', 'soundstimbuilder.tests'],
    url='https://github.com/gbeckers/soundstimbuilder',
    license='BSD-3',
    author='Gabriel J.L. Beckers',
    author_email='gabriel@gbeckers.nl',
    description='A package to create experimental sound stimuli',
    long_description=long_description,
    long_description_content_type="text/x-rst",
    python_requires='>=3.6',
    install_requires=['numpy'],
    data_files = [("", ["LICENSE"])],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Education',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Science/Research',
    ],
    project_urls={  # Optional
        'Source': 'https://github.com/gbeckers/soundstimbuilder',
    },
)
