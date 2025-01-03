# Generated by Django 4.2.17 on 2024-12-11 14:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('game', '0006_alter_tile_terrain'),
    ]

    operations = [
        migrations.AddField(
            model_name='tile',
            name='goods',
            field=models.JSONField(default=dict),
        ),
        migrations.CreateModel(
            name='QueuedAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(max_length=50)),
                ('details', models.JSONField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
