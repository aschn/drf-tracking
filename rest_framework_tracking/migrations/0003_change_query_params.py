# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ("rest_framework_tracking", "0002_add_status_code"),
    ]

    operations = [
        migrations.AlterField(
            'APIRequestLog',
            'query_params',
            models.TextField(db_index=True, null=True, blank=True),
        ),
    ]
