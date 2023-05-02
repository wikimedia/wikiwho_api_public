# -*- coding: utf-8 -*-
# Generated by Django 1.11.29 on 2023-05-02 14:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rest_framework_tracking', '0019_auto_20230501_1752'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apirequestlog',
            name='language',
            field=models.CharField(choices=[('', '-------'), ('en', 'English'), ('de', 'German'), ('eu', 'Basque'), ('tr', 'Turkish'), ('es', 'Spanish'), ('fr', 'French'), ('it', 'Italian'), ('hu', 'Hungarian'), ('id', 'Indonesian'), ('ja', 'Japanese'), ('pt', 'Portuguese')], default='', max_length=8),
        ),
    ]
