# Generated by Django 4.2.1 on 2023-08-30 10:52

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pb_visualizer', '0002_alter_rule_rule_family'),
    ]

    operations = [
        migrations.RenameField(
            model_name='election',
            old_name='vote_type',
            new_name='ballot_type',
        ),
    ]
