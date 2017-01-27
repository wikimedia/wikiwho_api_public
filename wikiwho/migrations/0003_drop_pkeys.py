# -*- coding: utf-8 -*-
# Generated manually.
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wikiwho', '0002_fake_fkeys'),
    ]

    operations = [
        # https://docs.djangoproject.com/en/1.10/ref/migration-operations/#django.db.migrations.operations.RunSQL
        migrations.RunSQL(
            sql='ALTER TABLE public.wikiwho_token DROP CONSTRAINT wikiwho_token_pkey;',
            reverse_sql='ALTER TABLE public.wikiwho_token ADD CONSTRAINT wikiwho_token_pkey PRIMARY KEY(id);'
        ),

        migrations.RunSQL(
            sql='ALTER TABLE public.wikiwho_revision DROP CONSTRAINT wikiwho_revision_pkey;',
            reverse_sql='ALTER TABLE public.wikiwho_revision ADD CONSTRAINT wikiwho_revision_pkey PRIMARY KEY(id);'
        ),
        migrations.RunSQL(
            sql='ALTER TABLE public.wikiwho_article DROP CONSTRAINT wikiwho_article_pkey;',
            reverse_sql='ALTER TABLE public.wikiwho_article ADD CONSTRAINT wikiwho_article_pkey PRIMARY KEY(id);'
        ),

        migrations.RunSQL(
            sql='ALTER TABLE public.wikiwho_revisioncontent DROP CONSTRAINT wikiwho_revisioncontent_pkey;',
            reverse_sql='ALTER TABLE public.wikiwho_revisioncontent ADD CONSTRAINT wikiwho_revisioncontent_pkey PRIMARY KEY(id);'
        ),
    ]
