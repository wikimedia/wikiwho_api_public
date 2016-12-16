# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-13 14:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wikiwho', '0007_indexes'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_revisionparagraph_position ON public.wikiwho_revisionparagraph USING btree ("position");',
            reverse_sql='DROP INDEX public.wikiwho_revisionparagraph_position'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_paragraphsentence_position ON public.wikiwho_paragraphsentence USING btree ("position");',
            reverse_sql='DROP INDEX public.wikiwho_paragraphsentence_position'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_sentencetoken_position ON public.wikiwho_sentencetoken USING btree ("position");',
            reverse_sql='DROP INDEX public.wikiwho_sentencetoken_position'
        )
    ]
