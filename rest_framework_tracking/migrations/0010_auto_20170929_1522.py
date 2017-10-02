# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-29 13:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest_framework_tracking', '0009_apirequestlog_language'),
    ]

    operations = [
        migrations.AddField(
            model_name='apirequestlog',
            name='view_class',
            field=models.CharField(default='WikiwhoApiView', max_length=200),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='apirequestlog',
            name='view_method',
            field=models.CharField(max_length=200),
        ),
    ]