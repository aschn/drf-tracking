# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rest_framework_tracking", "0002_auto_20170118_1713"),
    ]

    operations = [
        migrations.AddField(
            'APIRequestLog',
            'errors',
            models.TextField(null=True, blank=True),
        ),
    ]
