# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rest_framework_tracking", "0003_change_query_params"),
    ]

    operations = [
        migrations.AddField(
            'APIRequestLog',
            'errors',
            models.TextField(null=True, blank=True),
        ),
    ]
