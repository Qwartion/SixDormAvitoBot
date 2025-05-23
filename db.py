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
        response = supabase.table("users").insert(data).execute()
        return response


def record_count(chat_id):
    existing_record = supabase.table("record").select("*", count="exact").eq("chat_id", chat_id).execute()
    return existing_record.count

def create_record(new_record):
    data = {
        "chat_id": new_record[0],
        "category_id": new_record[1],
        "description": new_record[2],
        "new": new_record[3],
        "price": new_record[4]
    }
    supabase.table("record").insert(data).execute()