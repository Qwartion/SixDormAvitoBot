import telebot
from telebot import types
import os
from dotenv import load_dotenv
from db import *

load_dotenv()  # Загрузка токена из .env

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

btn_menu = types.KeyboardButton("Меню")

# Декоратор для обработки команды /start и /menu
@bot.message_handler(func=lambda m: m.text in ["Меню"] or m.text in ["/start", "/menu"]) 
def send_welcome(message):    
    save_user(message.chat.id, message.from_user.username)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("Мои объявления")
    btn2 = types.KeyboardButton("Чужие объявления")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Сейчас ты находишься в меню!", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "Мои объявления")
def my_ads(message):
    count = record_count(message.chat.id)
    if(count > 0):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width = 1)
        btn1 = types.KeyboardButton("Посмотреть записи")
        btn2 = types.KeyboardButton("Добавить запись")
        markup.add(btn1, btn2, btn_menu)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width = 1)
        btn1 = types.KeyboardButton("Добавить запись")
        markup.add(btn1, btn_menu)

    bot.send_message(message.chat.id, f"Количесвто ваших записей: {count}", reply_markup = markup)


new_record = [] # Временные данные

#################################### Создание новой записи ####################################
@bot.message_handler(func=lambda m: m.text == "Добавить запись")
def start_new_ads(message):
    new_record.append(message.chat.id)
    bot.send_message(
        message.chat.id,
        """Выберите категорию товара:
1. Одежда
2. Книги
3. Электроника
4. Мебель
5. Бытовая техника
6. Косметика
7. Еда
8. Канцелярия
9. Другое""",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.register_next_step_handler(message, process_category_step)


def process_category_step(message):
    if not message.text.isdigit() or int(message.text) < 1 or int(message.text) > 9: # isdigit() -- только цифры в сообщении
        bot.send_message(message.chat.id, "Пожалуйста, введите цифру от 1 до 9")
        bot.register_next_step_handler(message, process_category_step)  # Повторно регистрируем обработчик
        return

    new_record.append(int(message.text))
    bot.send_message(message.chat.id, "Введите описание товара:")
    bot.register_next_step_handler(message, process_description_step)

def process_description_step(message):
    description = message.text.strip()

    if len(description) < 3:
        bot.send_message(message.chat.id, "Описание слишком короткое.\nПопробуйте снова:")
        return bot.register_next_step_handler(message, process_description_step)

    new_record.append(description)
    bot.send_message(message.chat.id, "Каково состояние товара?\n1. Новый\n2. Б/у")
    bot.register_next_step_handler(message, process_status_step)

def process_status_step(message):
    if not message.text.isdigit() or int(message.text) < 1 or int(message.text) > 2:
        bot.send_message(message.chat.id, "Пожалуйста, введите цифру от 1 до 2")
        return bot.register_next_step_handler(message, process_status_step)

    if int(message.text) == 1: new_record.append(True)
    else: new_record.append(False)

    bot.send_message(message.chat.id, "Введите цену товара (только число):")
    bot.register_next_step_handler(message, process_price_step)

def process_price_step(message):
    if not message.text.isdigit() or int(message.text) < 0:
        bot.send_message(message.chat.id, "Некорректный ввод.\nПопробуйте снова:")
        return bot.register_next_step_handler(message, process_price_step)

    new_record.append(int(message.text))
    create_record(new_record)
    new_record.clear()
    bot.send_message(message.chat.id, "Объявление добавлено!")

    my_ads(message)
############################################################################################################


# Баловство

@bot.message_handler(func=lambda m: True) # принимает все сообщения которые не были пойманы до этого
def echo_all(message):
    bot.send_message(message.chat.id, f"""
Информация о тебе:
id = {message.from_user.id}
first_name = {message.from_user.first_name}
user_name = {message.from_user.username}
language code = {message.from_user.language_code}
""")



bot.polling()