# drf-tracking

[![build-status-image]][travis]
[![pypi-version]][pypi]

## Overview

Utils to log Django Rest Framework requests to the database

## Requirements

* Python (2.7, 3.3, 3.4)
* Django (1.6, 1.7, 1.8)
* Django REST Framework (2.4, 3.0, 3.1)

## Installation

Install using `pip`...

```bash
$ pip install drf-tracking
```

## Example

TODO: Write example.

## Testing

Install testing requirements.

```bash
$ pip install -r requirements.txt
```

Run with runtests.

```bash
$ ./runtests.py
```

You can also use the excellent [tox](http://tox.readthedocs.org/en/latest/) testing tool to run the tests against all supported versions of Python and Django. Install tox globally, and then simply run:

```bash
$ tox
```

## Documentation

To build the documentation, you'll need to install `mkdocs`.

```bash
$ pip install mkdocs
```

To preview the documentation:

```bash
$ mkdocs serve
Running at: http://127.0.0.1:8000/
```

To build the documentation:

```bash
$ mkdocs build
```


[build-status-image]: https://secure.travis-ci.org/aschn/drf-tracking.png?branch=master
[travis]: http://travis-ci.org/aschn/drf-tracking?branch=master
[pypi-version]: https://pypip.in/version/drf-tracking/badge.svg
[pypi]: https://pypi.python.org/pypi/drf-tracking
