# Generated by Django 4.2.17 on 2024-12-10 15:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('game', '0002_tile_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='tile',
            name='owner_id',
        ),
        migrations.RemoveField(
            model_name='tile',
            name='people',
        ),
        migrations.AddField(
            model_name='tile',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='tiles', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='tile',
            name='population',
            field=models.IntegerField(default=0),
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('money', models.IntegerField(default=100)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
