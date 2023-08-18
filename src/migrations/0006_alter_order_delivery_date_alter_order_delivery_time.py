# Generated by Django 4.2.4 on 2023-08-18 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('src', '0005_alter_order_delivery_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='delivery_date',
            field=models.DateField(auto_now_add=True, db_index=True, verbose_name='Дата доставки'),
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_time',
            field=models.IntegerField(choices=[(1, 'Как можно скорее'), (2, 'С 10:00 до 12:00'), (3, 'С 12:00 до 14:00'), (4, 'С 14:00 до 16:00'), (5, 'С 16:00 до 18:00'), (6, 'С 18:00 до 20:00')], verbose_name='Время доставки'),
        ),
    ]