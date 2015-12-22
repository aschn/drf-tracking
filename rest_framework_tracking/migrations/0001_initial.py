# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='APIRequestLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('requested_at', models.DateTimeField(db_index=True)),
                ('response_ms', models.PositiveIntegerField(default=0)),
                ('path', models.CharField(max_length=200, db_index=True)),
                ('remote_addr', models.GenericIPAddressField()),
                ('host', models.URLField()),
                ('method', models.CharField(max_length=10)),
                ('query_params', models.TextField(db_index=True)),
                ('data', models.TextField(null=True, blank=True)),
                ('response', models.TextField(null=True, blank=True)),
                ('user', models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
        ),
    ]
