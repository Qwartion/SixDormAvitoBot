from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

# Добавляем пользователя в БД, если его ещё нет
def save_user(chat_id, username):
    # Проверяем, существует ли уже пользователь с таким chat_id
    existing_user = supabase.table("users").select("*").eq("chat_id", chat_id).execute()
    # SELECT * FROM users WHERE chat_id = {chat_id};
    
    # Если записей нет, создаём
    if not existing_user.data:
        data = {
            "chat_id": chat_id,
            "username": username
        }
        supabase.table("users").insert(data).execute()
        # INSERT INTO users (chat_id, username) VALUES ({chat_id}, '{username}');
        print("Новый пользователь")
    elif existing_user.data[0]["username"] != username:
        supabase.table("users").update({"username": username}).eq("chat_id", chat_id).execute()
        # UPDATE users SET username = '{username}' WHERE chat_id = {chat_id};
        print("Имя измененно")



def record_count(chat_id):
    existing_record = supabase.table("record").select("*", count="exact").eq("chat_id", chat_id).eq("is_active", True).execute()
    # SELECT COUNT(*) FROM record WHERE chat_id = {chat_id} AND is_active = true;
    return existing_record.count

def create_record(record, file_id):
    supabase.table("record").insert(record).execute()
    if file_id != "":
        response = supabase.table("record").select("record_id").order("record_id", desc=True).limit(1).execute()
        supabase.table("photos").insert({"file_id": file_id, "file_unique_id": file_id, "record_id": response.data[0]["record_id"]}).execute()

def delete_record(record_id):
    supabase.table("record").update({"is_active": False}).eq("record_id", record_id).execute()
    # UPDATE record SET is_active = false WHERE record_id = {record_id};


def get_records(chat_id):
    response = supabase.table("record").select("*").eq("chat_id", chat_id).eq("is_active", True).execute()
    # SELECT * FROM record WHERE chat_id = {chat_id} AND is_active = true;
    return response.data

def get_photo(record_id):
    response = supabase.table("photos").select("file_id").eq("record_id", record_id).execute()
    # SELECT file_id FROM photos WHERE record_id = {record_id};
    return response.data


def id_to_username(chat_id):
    response = supabase.table("users").select("username").eq("chat_id", chat_id).execute()
    # SELECT username FROM users WHERE chat_id = {chat_id};
    return response.data[0]["username"]

def id_to_category(category_id):
    response = supabase.table("category").select("name").eq("category_id", category_id).execute()
    # SELECT name FROM category WHERE category_id = {category_id};
    return response.data[0]["name"]


### Вывод всех активных объявлений: ###
def get_all_active_records(exclude_chat_id):
    response = supabase.table("record").select("*").eq("is_active", True).neq("chat_id", exclude_chat_id).order("created_at", desc=False).execute()
    # SELECT * FROM record WHERE is_active = true AND chat_id <> {exclude_chat_id} ORDER BY created_at ASC;
    return response.data

### для фильтров: ###
def filter_records_combined(chat_id, category_id=None, max_price=None, tags=None):
    query = supabase.table("record").select("*").eq("is_active", True).neq("chat_id", chat_id)
    # SELECT * FROM record WHERE is_active = true AND chat_id <> {chat_id}

    if category_id is not None:
        query = query.eq("category_id", category_id)
        # AND category_id = {category_id}

    if max_price is not None:
        query = query.lte("price", max_price)
        # AND price <= {max_price}

    q_result = query.order("created_at", desc=True).execute()
    # ORDER BY created_at DESC;
    records = q_result.data

    if tags:
        filtered = []
        for record in records:
            desc = record.get("description", "").lower()
            if any(tag.lower() in desc for tag in tags):
                filtered.append(record)
        return filtered

    return records