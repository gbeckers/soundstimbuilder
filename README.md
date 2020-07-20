Soundstimbuilder
================

Soundstimbuilder is a python package for creating experimental sound stimuli.


Installation
------------
To install the latest development version, use pip with the latest GitHub
master: ::

    $ pip install git+https://github.com/gbeckers/soundstimbuilder@master

It is best to first create a separate Anaconda environment for installation, for now with a number of packages
with specific versions.

Most packages are in the default channel but you will also need one package from conda-forge. This channel may
need to be appended to conda's channel list (if it is already appended, then the next is still safe): ::

    $ conda config --append channels conda-forge

In a terminal, use the following to create an environment called "sndbld": ::

    $ conda create -n sndbld python=3.8 jupyter=1.0 scipy=1.4 darr=0.2.2 pandas=1.0 matplotlib=3.1

You can also create this environment from Anaconda Navigator, without using a terminal.

Testing
-------

To run the test suite:

.. code:: python

    >>> import soundstimbuilder as sb
    >>> sb.test()
    .
    ----------------------------------------------------------------------
    Ran 1 test in 0.000s
    
    OK
    <unittest.runner.TextTestResult run=1 errors=0 failures=0>
    
    >>>
    
Note that tests still have to be written, but the testing frame work is in place.