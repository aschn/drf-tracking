# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rest_framework_tracking", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            'APIRequestLog',
            'errors',
            models.TextField(null=True, blank=True),
        ),
    ]
