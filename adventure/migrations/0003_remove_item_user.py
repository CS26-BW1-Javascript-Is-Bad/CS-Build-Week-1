# Generated by Django 3.0.3 on 2020-03-03 00:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('adventure', '0002_item'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='user',
        ),
    ]
