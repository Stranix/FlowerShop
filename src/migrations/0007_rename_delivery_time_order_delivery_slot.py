# Generated by Django 4.2.4 on 2023-08-18 10:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0006_activeorder_alter_order_managers_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='delivery_time',
            new_name='delivery_slot',
        ),
    ]
