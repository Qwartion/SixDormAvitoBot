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
    "price": 0,
}
def reset_record():
    return EMPTY_RECORD.copy()

photo = ""

# Декоратор для обработки команды /start и /menu
@bot.message_handler(func=lambda m: m.text in ["Меню"] or m.text in ["/start", "/menu"]) 
def menu(message):    
    print("Запущен menu")
    save_user(message.chat.id, message.from_user.username)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Мои объявления")
    btn2 = types.KeyboardButton("Активные объявления")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id, "Сейчас ты находишься в меню!", reply_markup=markup)


@bot.message_handler(func=lambda m: m.text == "Мои объявления") # переход в ветку своих объявлений
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

    bot.send_message(message.chat.id, f"Количество ваших записей: {count}", reply_markup = markup)




#################################### Посмотреть мои записи ####################################
@bot.message_handler(func=lambda m: m.text == "Посмотреть записи")
def show_my_ads(message):
    print("Запущен show_my_ads")
    records = get_records(message.chat.id)
    for rec in records:
        file_id = get_photo(rec["record_id"])
        condition = "Новое" if rec.get("new") else "Б/у"
        msg = f'{rec["description"]}\n\n' + \
        f'Состояние: {condition}\n' + \
        f'Цена: {rec["price"]} рублей\n' + \
        f'Контакты: @{id_to_username(rec["chat_id"])}\n' + \
        f'Дата объявления: {rec["created_at"][:10]}\n' + \
        f'#{id_to_category(rec["category_id"])}'

        markup = types.InlineKeyboardMarkup()
        button = types.InlineKeyboardButton("Удалить", callback_data=f"delete_{rec['record_id']}")
        markup.add(button)

        if(file_id == []):
            bot.send_message(message.chat.id, msg, reply_markup=markup)
        else:
            bot.send_photo(chat_id = message.chat.id, photo = file_id[0]["file_id"], caption = msg, reply_markup=markup)
    
    my_ads(message)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_"))  # вызов удаления записи из бд
def callback_edit_record(call):
    record_id = int(call.data.split("_")[1])
    
    delete_record(record_id)
    bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    bot.answer_callback_query(call.id)
  
    





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


def process_category_step(message): # валидация выбора категории переход к добавлению фото
    print("Запущен process_category_step")
    if not message.text or not message.text.isdigit() or int(message.text) < 1 or int(message.text) > 9: # isdigit() -- только цифры в сообщении
        bot.send_message(message.chat.id, "Пожалуйста, введите цифру от 1 до 9")
        bot.register_next_step_handler(message, process_category_step)  # Повторно регистрируем обработчик
        return

    record["category_id"] = int(message.text)
    bot.send_message(message.chat.id, "Хотите добавить фото к объявлению?\n 1. Да\n 2. Нет")
    bot.register_next_step_handler(message, ask_add_photo)

def ask_add_photo(message): # нужно ли добавлять фото
    if message.text and message.text == "1":
        bot.send_message(message.chat.id, "Отправьте одно фото (сохранится только первое).")
        bot.register_next_step_handler(message, handle_photo_message)
    elif message.text and message.text == "2":
        bot.send_message(message.chat.id, "Введите описание товара:")
        bot.register_next_step_handler(message, process_description_step)
    elif not message.text or (message.text != "1" and message.text != "2"):
        bot.send_message(message.chat.id, "Пожалуйста, введите 1 или 2.")
        bot.register_next_step_handler(message, ask_add_photo)

def handle_photo_message(message):  # добавление фото и запрос на описание товара
    print("Запущен handle_photo_message")

    if not message.photo:
        bot.send_message(message.chat.id, "Вы не отправили фото. Попробуйте снова:")
        return bot.register_next_step_handler(message, handle_photo_message)

    global photo
    photo = message.photo[-1].file_id
    bot.send_message(message.chat.id, "Введите описание товара:")
    bot.register_next_step_handler(message, process_description_step)

def process_description_step(message):  # валидация описания, переход к состоянию
    print("Запущен process_description_step")
    if not message.text:
        bot.send_message(message.chat.id, "Некорректный ввод.\nПопробуйте снова:")
        return bot.register_next_step_handler(message, process_description_step)
    description = message.text.strip()

    if len(description) < 3:
        bot.send_message(message.chat.id, "Описание слишком короткое (надо больше 3 символов).\nПопробуйте снова:")
        return bot.register_next_step_handler(message, process_description_step)
    elif len(description) > 1024:
        bot.send_message(message.chat.id, "Описание слишком длинное (надо меньше 1024 символов).\nПопробуйте снова:")
        return bot.register_next_step_handler(message, process_description_step)

    record["description"] = description
    bot.send_message(message.chat.id, "Каково состояние товара?\n1. Новый\n2. Б/у")
    bot.register_next_step_handler(message, process_status_step)

def process_status_step(message):   # валидаця состояния и запрос цены
    print("Запущен process_status_step")
    if not message.text or not message.text.isdigit() or int(message.text) < 1 or int(message.text) > 2:
        bot.send_message(message.chat.id, "Пожалуйста, введите цифру от 1 до 2")
        return bot.register_next_step_handler(message, process_status_step)

    if int(message.text) == 2: record["new"] = False

    bot.send_message(message.chat.id, "Введите цену товара (только число):")
    bot.register_next_step_handler(message, process_price_step)

def process_price_step(message):    # валидация цены
    print("Запущен process_price_step")
    global record
    if not message.text or not message.text.isdigit() or int(message.text) < 0 or int(message.text) > 2000000:
        bot.send_message(message.chat.id, "Некорректный ввод. Допустимы ввод от 0 до 2 000 000.\nПопробуйте снова:")
        return bot.register_next_step_handler(message, process_price_step)

    record["price"] = int(message.text)
    finalize_record(message)

    
def finalize_record(message):   # добавление записи в бд
    global record, photo
    create_record(record, photo)
    bot.send_message(message.chat.id, "Объявление добавлено!")
    record = reset_record()
    photo = ""
    my_ads(message)
############################################################################################################



##################################### Просмотр активных записей ############################################

@bot.message_handler(func=lambda m: m.text == "Активные объявления")
def active_ads(message):
    print("Запущен active_ads")
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn1 = types.KeyboardButton("Показать все")
    btn2 = types.KeyboardButton("Фильтрация")
    markup.add(btn1, btn2, btn_menu)
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
    
#### Показать все ####
@bot.message_handler(func=lambda m: m.text == "Показать все")
def show_all_ads(message):
    print("Запущен show_all_ads")
    ads = get_all_active_records(message.chat.id)
    if not ads:
        bot.send_message(message.chat.id, "Объявления не найдены.")
        return
    send_ads_list(message, message.chat.id, ads)

#### Фильтрация ####
@bot.message_handler(func=lambda m: m.text == "Фильтрация")
def start_filtering(message):       # выбор категории
    print("Запущен start_filtering")
    bot.send_message(
        message.chat.id, 
        """Выберите категорию (введите цифру от 1 до 9 или 0, чтобы пропустить):
1. Одежда
2. Книги
3. Электроника
4. Мебель
5. Бытовая техника
6. Косметика
7. Еда
8. Канцелярия
9. Другое""", 
        reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(message, filter_step_category)

def filter_step_category(message):  # валидация категории и выбор цены
    print("Запущен filter_step_category")
    if not message.text or not message.text.isdigit() or not (0 <= int(message.text) <= 9):
        bot.send_message(message.chat.id, "Введите цифру от 0 до 9.")
        return bot.register_next_step_handler(message, filter_step_category)

    category_id = int(message.text)
    category_id = None if category_id == 0 else category_id
    bot.send_message(message.chat.id, "Введите максимальную цену (или -1, если не важно):")
    bot.register_next_step_handler(message, lambda msg: filter_step_price(msg, category_id))

def filter_step_price(message, category_id):    # валидация цены и выбор тегов
    print("Запущен filter_step_price")
    # try:
    #     max_price = int(message.text)
    # except ValueError:
    #     bot.send_message(message.chat.id, "Введите число (-1, если не важно).")
    #     return bot.register_next_step_handler(message, lambda msg: filter_step_price(msg, category_id))

    if not message.text or not (-1 <= int(message.text) <= 1000000):
        bot.send_message(message.chat.id, "Введите число от -1 до 2 000 000.")
        return bot.register_next_step_handler(message, lambda msg: filter_step_price(msg, category_id))
    max_price = int(message.text)
    max_price = None if max_price == -1 else max_price
    bot.send_message(message.chat.id, "Введите ключевые слова (теги) через пробел (или '-' если не важно):")
    bot.register_next_step_handler(message, lambda msg: filter_step_tags(msg, category_id, max_price))

def filter_step_tags(message, category_id, max_price):  # запись тегов и формирование данных для запроса к бд
    print("Запущен filter_step_tags")
    tags = message.text.strip().split() if message.text.strip() != "-" else []
    ads = filter_records_combined(
        chat_id=message.chat.id,
        category_id=category_id,
        max_price=max_price,
        tags=tags
    )
    if not ads:
        bot.send_message(message.chat.id, "Объявления не найдены.")
        active_ads(message)
        return
    send_ads_list(message, message.chat.id, ads)
    
def send_ads_list(message, chat_id, ads):    # отпарвка списка объявлений
    print("Запущен send_ads_list")
    for rec in ads:
        file_id = get_photo(rec["record_id"])
        condition = "Новое" if rec.get("new") else "Б/у"
        msg = f'{rec["description"]}\n\n' + \
              f'Состояние: {condition}\n' + \
              f'Цена: {rec["price"]} рублей\n' + \
              f'Контакты: @{id_to_username(rec["chat_id"])}\n' + \
              f'Дата объявления: {rec["created_at"][:10]}\n' + \
              f'#{id_to_category(rec["category_id"])}'
        if(file_id == []):
            bot.send_message(chat_id, msg)
        else:
            bot.send_photo(chat_id = chat_id, photo = file_id[0]["file_id"], caption = msg)
    active_ads(message)
############################################################################################################






# Баловство

@bot.message_handler(func=lambda m: True) # принимает все сообщения которые не были пойманы до этого
def alll(message):
    print("Запущен alll")
    bot.send_message(message.chat.id, f"Не реализовано. Возвращайся в меню")
    menu(message)





bot.polling()