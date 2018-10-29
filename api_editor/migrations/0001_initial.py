# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-10-29 11:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EditorDataDe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditorDataDeNotIndexed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditorDataEn',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditorDataEnNotIndexed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditorDataEs',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditorDataEsNotIndexed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditorDataEu',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditorDataEuNotIndexed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditorDataTr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EditorDataTrNotIndexed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('editor_name', models.CharField(default='', max_length=85)),
                ('o_adds', models.IntegerField()),
                ('o_adds_surv_48h', models.IntegerField()),
                ('dels', models.IntegerField()),
                ('dels_surv_48h', models.IntegerField()),
                ('reins', models.IntegerField()),
                ('reins_surv_48h', models.IntegerField()),
                ('persistent_o_adds', models.IntegerField()),
                ('persistent_actions', models.IntegerField()),
                ('adds_stopword_count', models.IntegerField(default=0)),
                ('dels_stopword_count', models.IntegerField(default=0)),
                ('reins_stopword_count', models.IntegerField(default=0)),
                ('article_id', models.IntegerField()),
                ('editor_id', models.IntegerField()),
                ('year_month', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
    ]