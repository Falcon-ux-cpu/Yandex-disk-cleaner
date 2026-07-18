import os
import requests
from datetime import datetime, timedelta, timezone

# Настройки берутся из секретов GitHub
TOKEN = os.getenv("YANDEX_DISK_TOKEN")
# Укажите папку (например, '/Загрузки' или '/' для всего диска)
TARGET_FOLDER = os.getenv("TARGET_FOLDER", "/")

HEADERS = {
    "Authorization": f"OAuth {TOKEN}",
    "Accept": "application/json"
}
BASE_URL = "https://cloud-api.yandex.net/v1/disk"

def get_old_files():
    """Получает список файлов старше 14 дней."""
    url = f"{BASE_URL}/resources"
    # Запрашиваем файлы, отсортированные по дате создания
    params = {
        "path": TARGET_FOLDER,
        "limit": 1000,
        "fields": "_embedded.items.path, _embedded.items.created, _embedded.items.type"
    }
    
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code != 200:
        print(f"Ошибка получения данных: {response.text}")
        return []

    data = response.json()
    items = data.get("_embedded", {}).get("items", [])
    
    now = datetime.now(timezone.utc)
    one_month_ago = now - timedelta(days=30)
    
    files_to_delete = []
    for item in items:
        # Пропускаем папки, если нужно удалять только файлы (или уберите проверку, чтобы удалять и папки)
        if item["type"] == "dir":
            continue
            
        # Парсим дату (Яндекс возвращает ISO формат, например, 2026-06-05T12:00:00Z)
        created_at = datetime.fromisoformat(item["created"].replace("Z", "+00:00"))
        
        if created_at < one_month_ago:
            files_to_delete.append(item["path"])
            
    return files_to_delete

def delete_files(file_paths):
    """Удаляет файлы (переносит в корзину)."""
    for path in file_paths:
        url = f"{BASE_URL}/resources"
        params = {"path": path, "permanently": "false"} # Сначала в корзину
        res = requests.delete(url, headers=HEADERS, params=params)
        if res.status_code in [202, 204]:
            print(f"Успешно удален: {path}")
        else:
            print(f"Не удалось удалить {path}: {res.text}")

def clear_trash():
    """Полностью очищает корзину."""
    url = f"{BASE_URL}/trash/resources"
    res = requests.delete(url, headers=HEADERS)
    if res.status_code in [202, 204]:
        print("Корзина успешно очищена!")
    elif res.status_code == 202:
        print("Очистка корзины запущена в асинхронном режиме.")
    else:
        print(f"Ошибка при очистке корзины: {res.text}")

if __name__ == "__main__":
    if not TOKEN:
        print("Ошибка: Токен YANDEX_DISK_TOKEN не найден в переменных окружения.")
        exit(1)
        
    print("Ищу старые файлы...")
    old_files = get_old_files()
    
    if old_files:
        print(f"Найдено файлов для удаления: {len(old_files)}")
        delete_files(old_files)
        print("Очищаю корзину...")
        clear_trash()
    else:
        print("Нет файлов старше 2 недель.")
        # На всякий случай чистим корзину, вдруг там что-то есть
        clear_trash()
