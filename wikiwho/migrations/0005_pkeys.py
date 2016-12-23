# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-12 14:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wikiwho', '0004_auto_20161212_1335'),
    ]

    operations = [
        # https://docs.djangoproject.com/en/1.10/ref/migration-operations/#django.db.migrations.operations.RunSQL
        migrations.RunSQL(
            sql='ALTER TABLE public.wikiwho_article ADD CONSTRAINT wikiwho_article_pkey PRIMARY KEY(id);',
            reverse_sql='ALTER TABLE public.wikiwho_article DROP CONSTRAINT wikiwho_article_pkey;'
        ),
        migrations.RunSQL(
            sql='ALTER TABLE public.wikiwho_revision ADD CONSTRAINT wikiwho_revision_pkey PRIMARY KEY(id);',
            reverse_sql='ALTER TABLE public.wikiwho_revision DROP CONSTRAINT wikiwho_revision_pkey;'
        ),

        # Until PK is added to Token, we indexed it.
        # CREATE INDEX wikiwho_token_id ON wikiwho_token USING btree (id);
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_token_id ON public.wikiwho_token USING btree (id);',
            reverse_sql='DROP INDEX public.wikiwho_token_id;'
        ),

        # TODO We need these PKs only for continue logic
        # migrations.RunSQL(
        #     sql='ALTER TABLE public.wikiwho_token ADD CONSTRAINT wikiwho_token_pkey PRIMARY KEY(id);',
        #     reverse_sql='ALTER TABLE public.wikiwho_token DROP CONSTRAINT wikiwho_token_pkey;'
        # ),
        # migrations.RunSQL(
        #     sql='ALTER TABLE public.wikiwho_sentence ADD CONSTRAINT wikiwho_sentence_pkey PRIMARY KEY(id);',
        #     reverse_sql='ALTER TABLE public.wikiwho_sentence DROP CONSTRAINT wikiwho_sentence_pkey;'
        # ),
        # migrations.RunSQL(
        #     sql='ALTER TABLE public.wikiwho_paragraph ADD CONSTRAINT wikiwho_paragraph_pkey PRIMARY KEY(id);',
        #     reverse_sql='ALTER TABLE public.wikiwho_paragraph DROP CONSTRAINT wikiwho_paragraph_pkey;'
        # ),

        # We dont need them
        # migrations.RunSQL(
        #     sql='ALTER TABLE public.wikiwho_revisionparagraph ADD CONSTRAINT wikiwho_revisionparagraph_pkey PRIMARY KEY(id);',
        #     reverse_sql='ALTER TABLE public.wikiwho_revisionparagraph DROP CONSTRAINT wikiwho_revisionparagraph_pkey;'
        # ),
        #
        # migrations.RunSQL(
        #     sql='ALTER TABLE public.wikiwho_paragraphsentence ADD CONSTRAINT wikiwho_paragraphsentence_pkey PRIMARY KEY(id);',
        #     reverse_sql='ALTER TABLE public.wikiwho_paragraphsentence DROP CONSTRAINT wikiwho_paragraphsentence_pkey;'
        # ),
        #
        # migrations.RunSQL(
        #     sql='ALTER TABLE public.wikiwho_sentencetoken ADD CONSTRAINT wikiwho_sentencetoken_pkey PRIMARY KEY(id);',
        #     reverse_sql='ALTER TABLE public.wikiwho_sentencetoken DROP CONSTRAINT wikiwho_sentencetoken_pkey;'
        # )
    ]

    # HACK: always fake. These fields are actually not FK on db.
    # This is done to use django's fk queries, emulated cascaded deletion
    def apply(self, project_state, schema_editor, collect_sql=False):
        return project_state.clone()
        # return project_state

    def unapply(self, project_state, schema_editor, collect_sql=False):
        return project_state.clone()
        # return project_state
