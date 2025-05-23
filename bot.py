import telebot
from telebot import types
import os
from dotenv import load_dotenv
from db import *

load_dotenv()  # Загрузка токена из .env

TOKEN = os.getenv("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)

btn_menu = types.KeyboardButton("Меню")
EMPTY_RECORD = {
    "chat_id": 0,
    "category_id": 0,
    "description": "    ",
    "new": True,
    "price": 0
}
def reset_record():
    return EMPTY_RECORD.copy()

# Декоратор для обработки команды /start и /menu
@bot.message_handler(func=lambda m: m.text in ["Меню"] or m.text in ["/start", "/menu"]) 
def menu(message):    
    print("Запущен menu")
    save_user(message.chat.id, message.from_user.username)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Мои объявления")
    btn2 = types.KeyboardButton("Чужие объявления")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Сейчас ты находишься в меню!", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "Мои объявления")
def my_ads(message):
    print("Запущен my_ads")
    count = record_count(message.chat.id)
    if(count > 0):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width = 1)
        btn1 = types.KeyboardButton("Посмотреть записи")
        btn2 = types.KeyboardButton("Добавить запись")
        markup.add(btn1, btn2, btn_menu)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width = 1)
        btn1 = types.KeyboardButton("Добавить запись")
        markup.add(btn1, btn_menu)

    bot.send_message(message.chat.id, f"Количесвто ваших записей: {count}", reply_markup = markup)




#################################### Посмотреть мои записи ####################################
@bot.message_handler(func=lambda m: m.text == "Посмотреть записи")
def show_my_ads(message):
    print("Запущен show_my_ads")
    records = get_records(message.chat.id)
    for rec in records:
        msg = f"{rec["description"]}\n\n" + \
        f"Цена: {rec["price"]} рублей\n" + \
        f"Контакты: @{id_to_username(rec["chat_id"])}\n" + \
        f"Дата объявления: {rec["created_at"][:10]}\n" + \
        f"#{id_to_category(rec["category_id"])}"

        bot.send_message(message.chat.id, msg)
    
    my_ads(message)






record = reset_record()

#################################### Создание новой записи ####################################
@bot.message_handler(func=lambda m: m.text == "Добавить запись")
def start_new_ads(message):
    print("Запущен start_new_ads")
    record["chat_id"] = message.chat.id
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
    print("Запущен process_category_step")
    if not message.text or not message.text.isdigit() or int(message.text) < 1 or int(message.text) > 9: # isdigit() -- только цифры в сообщении
        bot.send_message(message.chat.id, "Пожалуйста, введите цифру от 1 до 9")
        bot.register_next_step_handler(message, process_category_step)  # Повторно регистрируем обработчик
        return

    record["category_id"] = int(message.text)
    bot.send_message(message.chat.id, "Введите описание товара:")
    bot.register_next_step_handler(message, process_description_step)

def process_description_step(message):
    print("Запущен process_description_step")
    description = message.text.strip()

    if len(description) < 3:
        bot.send_message(message.chat.id, "Описание слишком короткое.\nПопробуйте снова:")
        return bot.register_next_step_handler(message, process_description_step)

    record["description"] = description
    bot.send_message(message.chat.id, "Каково состояние товара?\n1. Новый\n2. Б/у")
    bot.register_next_step_handler(message, process_status_step)

def process_status_step(message):
    print("Запущен process_status_step")
    if not message.text or not message.text.isdigit() or int(message.text) < 1 or int(message.text) > 2:
        bot.send_message(message.chat.id, "Пожалуйста, введите цифру от 1 до 2")
        return bot.register_next_step_handler(message, process_status_step)

    if int(message.text) == 2: record["new"] = False

    bot.send_message(message.chat.id, "Введите цену товара (только число):")
    bot.register_next_step_handler(message, process_price_step)

def process_price_step(message):
    print("Запущен process_price_step")
    global record
    if not message.text or not message.text.isdigit() or int(message.text) < 0 or int(message.text) > 2000000:
        bot.send_message(message.chat.id, "Некорректный ввод. Допустимы ввод от 0 до 2000000.\nПопробуйте снова:")
        return bot.register_next_step_handler(message, process_price_step)

    record["price"] = int(message.text)
    create_record(record)
    record = reset_record()
    bot.send_message(message.chat.id, "Объявление добавлено!")

    my_ads(message)
############################################################################################################








# Баловство

@bot.message_handler(func=lambda m: True) # принимает все сообщения которые не были пойманы до этого
def alll(message):
    print("Запущен alll")
    bot.send_message(message.chat.id, f"Не реализовано. Возвращайся в меню")
    menu(message)





bot.polling()