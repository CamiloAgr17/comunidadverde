# Generated by Django 5.2.4 on 2025-07-24 20:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inicio", "0002_notification"),
    ]

    operations = [
        migrations.AddField(
            model_name="post",
            name="imagen",
            field=models.ImageField(blank=True, null=True, upload_to="posts/"),
        ),
    ]
