# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-13 13:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wikiwho', '0005_pkeys'),
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
            model_name='revisionparagraph',
            name='revision_id',
            field=models.PositiveIntegerField(blank=False, null=False, db_column='revision_id'),
        ),
        migrations.RenameField(
            model_name='revisionparagraph',
            old_name='revision_id',
            new_name='revision',
        ),
        migrations.AlterField(
            model_name='revisionparagraph',
            name='revision',
            field=models.ForeignKey(blank=False, null=False, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='paragraphs', to='wikiwho.Revision'),
        ),

        migrations.AlterField(
            model_name='revisionparagraph',
            name='paragraph_id',
            field=models.UUIDField(blank=False, null=False, db_column='paragraph_id'),
        ),
        migrations.RenameField(
            model_name='revisionparagraph',
            old_name='paragraph_id',
            new_name='paragraph',
        ),
        migrations.AlterField(
            model_name='revisionparagraph',
            name='paragraph',
            field=models.ForeignKey(blank=False, null=False, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='revisions', to='wikiwho.Paragraph'),
        ),

        migrations.AlterField(
            model_name='paragraphsentence',
            name='paragraph_id',
            field=models.UUIDField(blank=False, null=False, db_column='paragraph_id'),
        ),
        migrations.RenameField(
            model_name='paragraphsentence',
            old_name='paragraph_id',
            new_name='paragraph',
        ),
        migrations.AlterField(
            model_name='paragraphsentence',
            name='paragraph',
            field=models.ForeignKey(blank=False, null=False, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='sentences', to='wikiwho.Paragraph'),
        ),

        migrations.AlterField(
            model_name='paragraphsentence',
            name='sentence_id',
            field=models.UUIDField(blank=False, null=False, db_column='sentence_id'),
        ),
        migrations.RenameField(
            model_name='paragraphsentence',
            old_name='sentence_id',
            new_name='sentence',
        ),
        migrations.AlterField(
            model_name='paragraphsentence',
            name='sentence',
            field=models.ForeignKey(blank=False, null=False, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='paragraphs', to='wikiwho.Sentence'),
        ),

        migrations.AlterField(
            model_name='sentencetoken',
            name='sentence_id',
            field=models.UUIDField(blank=False, null=False, db_column='sentence_id'),
        ),
        migrations.RenameField(
            model_name='sentencetoken',
            old_name='sentence_id',
            new_name='sentence',
        ),
        migrations.AlterField(
            model_name='sentencetoken',
            name='sentence',
            field=models.ForeignKey(blank=False, null=False, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='tokens', to='wikiwho.Sentence'),
        ),

        migrations.AlterField(
            model_name='sentencetoken',
            name='token_id',
            field=models.UUIDField(blank=False, null=False, db_column='token_id'),
        ),
        migrations.RenameField(
            model_name='sentencetoken',
            old_name='token_id',
            new_name='token',
        ),
        migrations.AlterField(
            model_name='sentencetoken',
            name='token',
            field=models.ForeignKey(blank=False, null=False, on_delete=django.db.models.deletion.CASCADE,
                                    related_name='sentences', to='wikiwho.Token'),
        ),

        migrations.AlterField(
            model_name='token',
            name='label_revision_id',
            field=models.PositiveIntegerField(blank=False, null=False, db_column='label_revision_id'),
        ),
        migrations.RenameField(
            model_name='token',
            old_name='label_revision_id',
            new_name='label_revision',
        ),
        migrations.AlterField(
            model_name='token',
            name='label_revision',
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