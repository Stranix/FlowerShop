from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class Event(models.Model):
    name = models.CharField(
        'Название события',
        max_length=100
    )

    class Meta:
        verbose_name = 'Событие'
        verbose_name_plural = 'События'

    def __str__(self):
        return self.name


class Client(models.Model):
    name = models.CharField(
        'Имя',
        max_length=200
    )
    phonenumber = PhoneNumberField(
        verbose_name='Телефон',
        db_index=True
    )

    class Meta:
        verbose_name = 'Клиент'
        verbose_name_plural = 'Клиенты'

    def __str__(self):
        return self.name


class Bouquet(models.Model):
    name = models.CharField(
        'Название букета',
        max_length=100,
        unique=True,
        db_index=True
    )
    image = models.ImageField(
        'Картинка'
    )
    price = models.IntegerField(
        'Цена',
        db_index=True
    )
    description = models.TextField(
        'Описание',
        max_length=5000
    )
    compound = models.TextField(
        'Состав',
        max_length=5000
    )
    events = models.ManyToManyField(
        Event,
        verbose_name='Для событий',
        related_name='bouquet'
    )

    class Meta:
        verbose_name = 'Букет'
        verbose_name_plural = 'Букеты'

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS = (
        ('in_delivery', 'В доставке'),
        ('delivered', 'Доставлен')
    )
    bouquet = models.ForeignKey(
        Bouquet,
        verbose_name='Заказанный букет',
        on_delete=models.DO_NOTHING,
        related_name='orders'
    )
    price = models.IntegerField(
        'Цена букета'
    )
    client = models.ForeignKey(
        Client,
        verbose_name='Клиент',
        on_delete=models.DO_NOTHING,
        related_name='orders'
    )
    delivery_date = models.DateField(
        'Дата доставки',
        db_index=True
    )
    delivery_time = models.TimeField(
        'Время доставки'
    )
    address = models.CharField(
        'Адрес доставки',
        max_length=1000
    )
    comment = models.CharField(
        'Комментарий',
        max_length=1000,
        blank=True,
        default=''
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.bouquet} - {self.address}'