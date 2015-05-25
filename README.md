# drf-tracking

[![build-status-image]][travis]
[![pypi-version]][pypi]
[![Requirements Status](https://requires.io/github/aschn/drf-tracking/requirements.svg?branch=master)](https://requires.io/github/aschn/drf-tracking/requirements/?branch=master)

## Overview

Utils to log Django Rest Framework requests to the database

## Requirements

* Python 2.7
* Django (1.7, 1.8)
* Django REST Framework (3.0, 3.1)

## Installation

Install using `pip`...

```bash
$ pip install drf-tracking
```

Register with your Django project by adding `rest_framework_tracking`
to the `INSTALLED_APPS` list in your project's `settings.py` file.
Then run the migrations for the `APIRequestLog` model:

```bash
$ python manage.py migrate
```

## Usage

Add the `rest_framework_tracking.mixins.LoggingMixin` to any DRF view
to create an instance of `APIRequestLog` every time the view is called.

For instance:
```python
# views.py
from rest_framework import generics
from rest_framework_tracking.mixins import LoggingMixin

class LoggingView(LoggingMixin, generics.GenericAPIView):
    def get(self, request):
        return Response('with logging')
```

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
