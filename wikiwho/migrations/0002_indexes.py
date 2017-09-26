# -*- coding: utf-8 -*-
# Generated manually.
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    """
    This migration presents only indexes that we want to add manually to editor tables.
    """

    dependencies = [
        ('wikiwho', '0001_initial'),
    ]

    operations = [
        # However there are cases where a multi-column index clearly makes sense. An index on columns (a, b) can be
        # used by queries containing WHERE a = x AND b = y, or queries using WHERE a = x only,
        # but will not be used by a query using WHERE b = y. So if this matches the query patterns of your application,
        # the multi-column index approach is worth considering. Also note that in this case creating an index on 'a'
        # alone would be redundant.
        # migrations.RunSQL(
        #     sql='CREATE INDEX wikiwho_revision_article_id ON public.wikiwho_revision USING btree (article_id);',
        #     reverse_sql='DROP INDEX public.wikiwho_revision_article_id;'
        # ),
        # An index stored in ascending order with nulls first can satisfy either ORDER BY x ASC NULLS LAST or
        # ORDER BY x DESC NULLS FIRST depending on which direction it is scanned in.
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_editordataen_article_id ON public.wikiwho_editordataen USING btree (article_id);',
            reverse_sql='DROP INDEX public.wikiwho_editordataen_article_id;'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_editordataen_year_month ON public.wikiwho_editordataen USING btree (year_month);',  # by default ASC NULLS LAST
            reverse_sql='DROP INDEX public.wikiwho_editordataen_year_month;'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_editordataen_editor_id_ym ON public.wikiwho_editordataen USING btree (editor_id, year_month);',
            reverse_sql='DROP INDEX public.wikiwho_editordataen_editor_id_ym;'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_editordataeu_article_id ON public.wikiwho_editordataeu USING btree (article_id);',
            reverse_sql='DROP INDEX public.wikiwho_editordataeu_article_id;'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_editordataeu_year_month ON public.wikiwho_editordataeu USING btree (year_month);',
            reverse_sql='DROP INDEX public.wikiwho_editordataeu_year_month;'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_editordataeu_editor_id_ym ON public.wikiwho_editordataeu USING btree (editor_id, year_month);',
            reverse_sql='DROP INDEX public.wikiwho_editordataeu_editor_id_ym;'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_editordatade_article_id ON public.wikiwho_editordatade USING btree (article_id);',
            reverse_sql='DROP INDEX public.wikiwho_editordatade_article_id;'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_editordatade_year_month ON public.wikiwho_editordatade USING btree (year_month);',
            reverse_sql='DROP INDEX public.wikiwho_editordatade_year_month;'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_editordatade_editor_id_ym ON public.wikiwho_editordatade USING btree (editor_id, year_month);',
            reverse_sql='DROP INDEX public.wikiwho_editordatade_editor_id_ym;'
        ),
    ]

    # HACK: always fake.
    # def apply(self, project_state, schema_editor, collect_sql=False):
    #     return project_state.clone()
    #     # return project_state
    #
    # def unapply(self, project_state, schema_editor, collect_sql=False):
    #     return project_state.clone()
    #     # return project_state
