# Generated by Django 5.2 on 2025-04-21 19:38

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Subscription', '0009_subscriptionprice'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='subscriptionprice',
            options={'ordering': ['order', 'featured', '-updated']},
        ),
        migrations.AddField(
            model_name='subscriptionprice',
            name='featured',
            field=models.BooleanField(default=True, help_text='Featured on Django pricing page'),
        ),
        migrations.AddField(
            model_name='subscriptionprice',
            name='order',
            field=models.IntegerField(default=-1, help_text='Ordering on Django pricing page'),
        ),
        migrations.AddField(
            model_name='subscriptionprice',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='subscriptionprice',
            name='updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
