# Generated by Django 3.1.5 on 2021-03-05 22:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_auto_20210305_1855"),
        ("guests", "0002_auto_20210305_2341"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="EventGuestLink",
            new_name="EventGuestShare",
        ),
    ]
