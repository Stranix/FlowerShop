import datetime

import phonenumbers
from django.db.models import Max

from telegram import Update
from telegram import ReplyKeyboardRemove
from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton

from telegram.ext import CallbackContext
from telegram.ext import ConversationHandler

from src.bot import utils
from src.bot.states import CustomerState
from src.bot.utils import get_event_list_from_base

from src.models import Bouquet, Order, Consultation, Client, Event
from src.utils import get_recommended_bouquet


def start_for_customer(update: Update, context: CallbackContext):
    button_names = get_event_list_from_base()
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='К какому событию готовимся? \n'
             'Выберите один из вариантов, либо укажите свой',
        reply_markup=utils.create_tg_keyboard_markup(
            button_names,
            buttons_per_row=3,
        )
    )
    return CustomerState.AMOUNT_CHOICE


def amount_choice(update: Update, context: CallbackContext):
    user_data = context.user_data
    event_name = update.message.text
    user_data['event'] = Event.objects.get(name=event_name)
    button_names = [
        'До 1 000 руб',
        '1 000 - 5 000 руб',
        'от 5 000 руб',
        'не важно'
    ]

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='На какую сумму рассчитываете?',
        reply_markup=utils.create_tg_keyboard_markup(
            button_names,
            buttons_per_row=3,
        )
    )
    return CustomerState.BOUQUET


def get_bouquet_flowers(update: Update, context: CallbackContext):
    user_data = context.user_data
    event = user_data['event']

    match update.message.text:
        case 'До 1 000 руб': amounts = '1-1000'
        case '1 000 - 5 000 руб': amounts = '1000-5000'
        case 'от 5 000 руб': amounts = '5000-999999999'
        case _: amounts = '0-999999999'

    bouquet = get_recommended_bouquet(event.id, tuple(amounts.split('-')))

    if not bouquet:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='К сожалению нет подходящего букета для вас.\n'
            'Попробуйте еще раз задать фильтр с начала /start'
        )
        return ConversationHandler.END

    pay_button = InlineKeyboardButton(
        'Оплата',
        callback_data=f'payment{bouquet.id}',
    )
    context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=bouquet.image,
        reply_markup=InlineKeyboardMarkup([[pay_button]]),
        caption=f'Описание: {bouquet.description}\n\n'
                f'Состав: {bouquet.compound}\n\n'
                f'Стоимость: {bouquet.price}',
    )

    button_names = [
        'Заказать консультацию',
        'Посмотреть всю коллекцию'
    ]

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Хотите что-то более специальное?\nПодберите другой букет из '
             'нашей коллекции или закажите личную консультацию',
        reply_markup=utils.create_tg_keyboard_markup(button_names)
    )
    return CustomerState.CHOICE_BOUQUET


def start_payment(update: Update, context: CallbackContext):
    if update.callback_query.data.startswith('prev'):
        context.bot.delete_message(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )
        bouquet_id = update.callback_query.data.split('_')[1]
        return view_all_bouquets(update, context, int(bouquet_id) - 1)

    if update.callback_query.data.startswith('next'):
        context.bot.delete_message(
            chat_id=update.callback_query.message.chat_id,
            message_id=update.callback_query.message.message_id
        )
        bouquet_id = update.callback_query.data.split('_')[1]
        return view_all_bouquets(update, context, int(bouquet_id) + 1)

    if update.callback_query.data.startswith('payment'):
        user_data = context.user_data
        user_data['bouquet_id'] = update.callback_query.data[7:]
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Как вас зовут?'
        )
        return CustomerState.PAYMENT


def choice_bouquet(update: Update, context: CallbackContext):
    if update.message.text == 'Посмотреть всю коллекцию':
        return view_all_bouquets(update, context)

    if update.message.text == 'Заказать консультацию':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Укажите номер телефона, и наш флорист перезвонит вам в '
                 'течение 20 минут',
        )
        return CustomerState.CONSULTATION

    return get_bouquet_flowers(update, context)


def process_consultation_choice(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data['name'] = update.message.from_user.username
    user_data['phonenumber'] = update.message.text
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Спасибо, ваша заявка на консультацию принята, '
             'мы скоро свяжемся с вами',
    )
    client, _ = Client.objects.get_or_create(
        name=user_data['name'],
        phonenumber=user_data['phonenumber']
    )
    Consultation.objects.create(client=client)

    return ConversationHandler.END


def get_customer_address(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data['name'] = update.message.text
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Введите Ваш адрес',
    )
    return CustomerState.ADDRESS


def get_phone_number(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data['address'] = update.message.text
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Введите Ваш номер телефона',
    )
    return CustomerState.PHONE_NUMBER


def get_delivery_date(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data['phonenumber'] = update.message.text

    try:
        parsed_phonenumber = phonenumbers.parse(
            user_data['phonenumber'],
            'RU'
        )
    except phonenumbers.phonenumberutil.NumberParseException:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Номер телефона был введен неправильно, повторите попытку',
        )
        return CustomerState.PHONE_NUMBER

    if phonenumbers.is_valid_number(parsed_phonenumber):
        user_data['phonenumber'] = phonenumbers.format_number(
            parsed_phonenumber,
            phonenumbers.PhoneNumberFormat.E164
        )
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Введеный Вами номер телефона не существует. Попробуйте '
                 'ввести через +7',
        )
        return CustomerState.PHONE_NUMBER

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Введите дату доставки в формате: год-месяц-день',
    )
    return CustomerState.DELIVERY_DATE


def get_delivery_time(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data['delivery_date'] = update.message.text

    try:
        user_data['delivery_date'] = datetime.datetime.strptime(
            user_data['delivery_date'],
            '%Y-%m-%d').date()
    except ValueError:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Попробуйте ещё раз, например 2023-06-15',
        )
        return CustomerState.DELIVERY_DATE

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Выберите время доставки:\n'
             '1. Как можно скорее\n'
             '2. С 10:00 до 12:00\n'
             '3. С 12:00 до 14:00\n'
             '4. С 14:00 до 16:00\n'
             '5. С 16:00 до 18:00\n'
             '6. С 18:00 до 20:00'
             )
    return CustomerState.CHECK_INFO


def check_customer_information(update: Update, context: CallbackContext):
    user_data = context.user_data
    user_data['delivery_time'] = update.message.text

    if int(user_data['delivery_time']) not in (1, 2, 3, 4, 5, 6):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Выберите вариант от 1 до 6',
        )
        return CustomerState.CHECK_INFO

    button_names = [
        'Да',
        'Нет'
    ]
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Верны ли Ваши данные?\n Адрес: {user_data["address"]}\n'
             f'Номер телефона: {user_data["phonenumber"]}',
        reply_markup=utils.create_tg_keyboard_markup(
            button_names,
            buttons_per_row=2,
        )
    )
    return CustomerState.CREATE_ORDER


def create_order(update: Update, context: CallbackContext):
    user_data = context.user_data

    if update.message.text == 'Нет':
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Введите Ваш адрес',
            )
        return CustomerState.ADDRESS

    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Спасибо за уделенное время. Информация о доставке \n '
             'Для повторной сессии напишите в чат /start',
    )
    bouquet = Bouquet.objects.get(pk=user_data['bouquet_id'])
    client, _ = Client.objects.get_or_create(
        name=user_data['name'],
        phonenumber=user_data['phonenumber']
    )
    Order.objects.create(bouquet=bouquet,
                         price=bouquet.price,
                         client=client,
                         delivery_date=user_data['delivery_date'],
                         address=user_data['address'],
                         delivery_slot=int(user_data['delivery_time']),
                         )
    return ConversationHandler.END


def cancel(update, _):
    update.message.reply_text(
        'Спасибо за уделенное Вами время\n'
        'Если хотите продолжить работу введите команду\n'
        '/start',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def view_all_bouquets(
        update: Update,
        context: CallbackContext,
        bouquet_id: int = 1
):
    while True:
        try:
            bouquet = Bouquet.objects.get(id=bouquet_id)
            pay_button = InlineKeyboardButton(
                'Оплата',
                callback_data=f'payment{bouquet.id}',
            )
            prev_button = InlineKeyboardButton(
                '<<',
                callback_data=f'prev_{bouquet.id}',
            )
            next_button = InlineKeyboardButton(
                '>>',
                callback_data=f'next_{bouquet.id}',
            )
            first_row_button = [prev_button, pay_button, next_button]
            buttons = InlineKeyboardMarkup([first_row_button])
            context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=bouquet.image,
                    reply_markup=buttons,
                    caption=f'Описание: {bouquet.description}\n\n'
                            f'Состав: {bouquet.compound}\n\n'
                            f'Стоимость: {bouquet.price}',
            )
            return
        except Bouquet.DoesNotExist:
            max_id = Bouquet.objects.aggregate(max_id=Max("id"))['max_id']
            if bouquet_id < max_id:
                bouquet_id += 1
            else:
                bouquet_id -= 1
