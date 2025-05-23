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
    
    # Если записей нет, создаём
    if not existing_user.data:
        data = {
            "chat_id": chat_id,
            "username": username
        }
        supabase.table("users").insert(data).execute()
        print("Новый пользователь")
    elif existing_user.data[0]["username"] != username:
        supabase.table("users").update({"username": username}).eq("chat_id", chat_id).execute()
        print("Имя измененно")



def record_count(chat_id):
    existing_record = supabase.table("record").select("*", count="exact").eq("chat_id", chat_id).execute()
    return existing_record.count

def create_record(record):
    supabase.table("record").insert(record).execute()

def get_records(chat_id):
    response = supabase.table("record").select("*").eq("chat_id", chat_id).execute()
    return response.data

def id_to_username(chat_id):
    response = supabase.table("users").select("username").eq("chat_id", chat_id).execute()
    return response.data[0]["username"]

def id_to_category(category_id):
    response = supabase.table("category").select("name").eq("category_id", category_id).execute()
    return response.data[0]["name"]