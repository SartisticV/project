# Generated by Django 4.2.17 on 2024-12-19 15:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_universalgoods'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='queuedaction',
            options={'verbose_name': 'Queued Action', 'verbose_name_plural': 'Queued Actions'},
        ),
        migrations.AlterModelOptions(
            name='universalgoods',
            options={'verbose_name': 'Universal Good', 'verbose_name_plural': 'Universal Goods'},
        ),
    ]
