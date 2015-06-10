<div class="badges">
    <a href="http://travis-ci.org/aschn/drf-tracking">
        <img src="https://travis-ci.org/aschn/drf-tracking.svg?branch=master">
    </a>
    <a href="https://pypi.python.org/pypi/drf-tracking">
        <img src="https://pypip.in/version/drf-tracking/badge.svg">
    </a>
</div>

---

# drf-tracking

Utilities to log Django Rest Framework requests to the database.

---

## Overview

drf-tracking provides a Django model and DRF view mixin that work together to log Django Rest Framework requests to the database. You'll get these attributes for every request/response cycle to a view that uses the mixin:

 Model field name | Description | Model field type
------------------|-------------|-----------------
`user` | User if authenticated, None if not | Foreign Key
`requested_at` | Date-time that the request was made | DateTimeField
`response_ms` | Number of milliseconds spent in view code | PositiveIntegerField
`path` | Target URI of the request, e.g., `"/api/"` | CharField
`remote_addr` | IP address where the request originated, e.g., `"127.0.0.1"` | GenericIPAddressField
`host` | Originating host of the request, e.g., `"example.com"` | URLField
`method` | HTTP method, e.g., `"GET"` | CharField
`query_params` | Dictionary of request query parameters, as text | TextField
`data` | Dictionary of POST data (JSON or form), as text | TextField
`response` | JSON response data | TextField
`status_code` | HTTP status code, e.g., `200` or `404` | PositiveIntegerField

## Requirements

* Python (2.7, 3.3, 3.4)
* Django (1.6, 1.7)

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
