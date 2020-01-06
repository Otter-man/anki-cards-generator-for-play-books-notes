
MyModule
========

Sample Python module.
Just clone this repository and change all `mnemocards` to your module name. Also search for `mnemocards` because it's used in some URLs that point to the repository.


Getting started
---------------

These instructions will get you a copy of the project up and running on your local machine.


### Prerequisites

The minimum Python version supported is version 3.


### Install

Install the package in a dev environment with:

    python setup.py develop

This line will automatically install all the dependencies.


## Upload module to PyPi

Generate dist files:

    python setup.py sdist bdist_wheel

Upload the generated files with Twine using your PyPi account:

    python -m twine upload dist/*


## Running the tests

Run the automated tests with:

    python -m pytest


Contributing
------------

Please read [CONTRIBUTING.md](https://github.com/guiferviz/mnemocards/blob/master/CONTRIBUTING.md) for details on our code of conduct, and the process for submitting pull requests.


Versioning
----------

We use [SemVer](http://semver.org/) for versioning.


Authors
-------

List of main contributors:

* **Guille** - [guiferviz](https://github.com/guiferviz)

For a full list of contributors see [AUTHORS](https://github.com/guiferviz/mnemocards/blob/master/AUTHORS.md).


License
-------

This project is licensed under the **MIT License**, see the [LICENSE](https://github.com/guiferviz/mnemocards/blob/master/LICENSE) file for details.


Acknowledgments
---------------

 * Attribution to anyone whose code was used.
 * You've been inpired by...
 * Say thanks to someone.
