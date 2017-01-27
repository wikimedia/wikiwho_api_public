# -*- coding: utf-8 -*-
# Generated manually.
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    """
    This migration presents only indexes that we want to add manually.
    """
    # TODO pk constraints

    dependencies = [
        ('wikiwho', '0003_drop_pkeys'),
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
            sql='CREATE INDEX wikiwho_revision_timestamp ON public.wikiwho_revision USING btree ("timestamp");',  # by default ASC NULLS LAST
            reverse_sql='DROP INDEX public.wikiwho_revision_timestamp;'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_revision_article_id_ts ON public.wikiwho_revision USING btree (article_id, "timestamp" DESC);',
            reverse_sql='DROP INDEX public.wikiwho_revision_article_id_ts;'
        ),
        migrations.RunSQL(
            # CREATE INDEX orders_unbilled_index ON orders(order_nr) WHERE billed is not true;
            sql='CREATE INDEX wikiwho_is_article_id ON public.wikiwho_article (id) WHERE is_article is true;',
            reverse_sql='DROP INDEX public.wikiwho_is_article_id;'
        ),

        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_token_token_id ON public.wikiwho_token USING btree (token_id);',
            reverse_sql='DROP INDEX public.wikiwho_token_token_id'
        ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_token_article_id ON public.wikiwho_token USING btree (article_id);',
            reverse_sql='DROP INDEX public.wikiwho_token_article_id'
        ),

        # we need this indexes for deleted_content queries
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_token_origin_rev_id ON public.wikiwho_token USING btree (origin_rev_id);',
            reverse_sql='DROP INDEX public.wikiwho_token_origin_rev_id'
        ),
        # migrations.RunSQL(
        #     sql='CREATE INDEX wikiwho_token_token_id ON public.wikiwho_token USING btree (token_id);',
        #     reverse_sql='DROP INDEX public.wikiwho_token_token_id;'
        # ),
        migrations.RunSQL(
            sql='CREATE INDEX wikiwho_token_last_rev_id ON public.wikiwho_token USING btree (last_rev_id);',
            reverse_sql='DROP INDEX public.wikiwho_token_last_rev_id;'
        ),
        # TODO should we do this only for len comparision?
        # migrations.RunSQL(
        #     sql='CREATE INDEX wikiwho_token_label_outbound ON public.wikiwho_token USING gin (outbound);',
        #     reverse_sql='DROP INDEX public.wikiwho_token_label_outbound;'
        # )
    ]

    # HACK: always fake.
    def apply(self, project_state, schema_editor, collect_sql=False):
        return project_state.clone()
        # return project_state

    def unapply(self, project_state, schema_editor, collect_sql=False):
        return project_state.clone()
        # return project_state
