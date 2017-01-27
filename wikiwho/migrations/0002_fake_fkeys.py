# -*- coding: utf-8 -*-
# Generated manually
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wikiwho', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='revision',
            name='article_id',
            field=models.PositiveIntegerField(blank=False, null=False, db_column='article_id'),
        ),
        migrations.RenameField(
            model_name='revision',
            old_name='article_id',
            new_name='article',
        ),
        migrations.AlterField(
            model_name='revision',
            name='article',
            field=models.ForeignKey(blank=False, null=False, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='revisions', to='wikiwho.Article'),
        ),

        migrations.AlterField(
            model_name='token',
            name='article_id',
            field=models.PositiveIntegerField(blank=False, null=False, db_column='article_id'),
        ),
        migrations.RenameField(
            model_name='token',
            old_name='article_id',
            new_name='article',
        ),
        migrations.AlterField(
            model_name='token',
            name='article',
            field=models.ForeignKey(blank=False, null=False, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='tokens', to='wikiwho.Article'),
        ),

        migrations.AlterField(
            model_name='token',
            name='origin_rev_id',
            field=models.PositiveIntegerField(blank=False, null=False, db_column='origin_rev_id'),
        ),
        migrations.RenameField(
            model_name='token',
            old_name='origin_rev_id',
            new_name='origin_rev',
        ),
        migrations.AlterField(
            model_name='token',
            name='origin_rev',
            field=models.ForeignKey(blank=False, null=False, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='introduced_tokens', to='wikiwho.Revision'),
        ),
    ]

    # HACK: always fake. These fields are actually not FK on db.
    # This is done to use django's fk queries, emulated cascaded deletion
    def apply(self, project_state, schema_editor, collect_sql=False):
        return project_state.clone()
        # return project_state

    def unapply(self, project_state, schema_editor, collect_sql=False):
        return project_state.clone()
        # return project_state
