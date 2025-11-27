import os
import requests

# ==============================
# Загрузка ENV
# ==============================
CONFLUENCE_BASE_URL = os.getenv("CONFLUENCE_BASE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")
CONFLUENCE_SPACE_KEY = os.getenv("CONFLUENCE_SPACE_KEY")

auth = (CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN)


# =====================================================================================
# 0. Генерация короткого title (5 слов) + URL-safe версии
# =====================================================================================
def make_safe_title(raw: str):
    if not raw:
        return "New Project", "New-Project"

    words = raw.split()

    # Берём первые 5 слов
    short = " ".join(words[:5])

    # Убираем запрещённые символы
    for bad in [":", "/", "\\", "|", "*", "?", "\"", "<", ">"]:
        short = short.replace(bad, "")

    # URL-friendly
    safe_url = short.replace(" ", "-")

    return short, safe_url


# =====================================================================================
# 1. Поиск страницы по названию
# =====================================================================================
def find_page_by_title(title: str):
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
    params = {
        "title": title,
        "spaceKey": CONFLUENCE_SPACE_KEY,
        "expand": "version"
    }

    resp = requests.get(url, params=params, auth=auth)

    if resp.status_code != 200:
        print("[Confluence] Search failed:", resp.text)
        return None

    data = resp.json()
    if data.get("size", 0) == 0:
        return None

    return data["results"][0]


# =====================================================================================
# 2. Обновление существующей страницы
# =====================================================================================
def update_page(page, title, content_html):
    page_id = page["id"]
    new_version = page["version"]["number"] + 1

    payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {
            "storage": {
                "value": content_html,
                "representation": "storage"
            }
        },
        "version": {"number": new_version}
    }

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}"
    resp = requests.put(url, json=payload, auth=auth)

    if resp.status_code not in [200, 201]:
        print("[Confluence] Update error:", resp.text)
        return None

    return page_id


# =====================================================================================
# 3. Создание новой страницы
# =====================================================================================
def create_page(title, content_html):
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content"

    payload = {
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {
            "storage": {
                "value": content_html,
                "representation": "storage"
            }
        }
    }

    resp = requests.post(url, json=payload, auth=auth)

    if resp.status_code not in [200, 201]:
        print("[Confluence] Create error:", resp.text)
        return None

    return resp.json()["id"]


# =====================================================================================
# 4. Загрузка PDF-файла как вложения
# =====================================================================================
def upload_pdf_attachment(page_id, pdf_path):
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/attachment"

    files = {
        "file": (os.path.basename(pdf_path), open(pdf_path, "rb"), "application/pdf")
    }

    headers = {"X-Atlassian-Token": "no-check"}

    resp = requests.post(url, files=files, headers=headers, auth=auth)

    if resp.status_code not in [200, 201]:
        print("[Confluence] Upload error:", resp.text)
        return False

    return True


# =====================================================================================
# 5. Главная функция: создать/обновить страницу + загрузить PDF + вернуть красивый URL
# =====================================================================================
def create_brd_page(title_raw: str, brd_text: str, pdf_path: str):

    # 1. Генерация короткого title
    short_title, safe_url_title = make_safe_title(title_raw)

    # Финальное название страницы в Confluence
    title = f"BRD – {short_title}"

    # HTML-контент
    content_html = f"""
    <h1>{title}</h1>
    <p>Автоматически сгенерированный BRD документ.</p>
    <pre>{brd_text}</pre>
    """

    # 2. Проверяем, существует ли страница
    existing = find_page_by_title(title)

    if existing:
        page_id = update_page(existing, title, content_html)
        print("[Confluence] Updated existing page:", page_id)
    else:
        page_id = create_page(title, content_html)
        print("[Confluence] Created new page:", page_id)

    if not page_id:
        return None

    # 3. Загружаем PDF
    upload_pdf_attachment(page_id, pdf_path)

    # 4. Формируем красивую ссылку
    pretty_url = f"{CONFLUENCE_BASE_URL}/spaces/{CONFLUENCE_SPACE_KEY}/pages/{page_id}/{safe_url_title}"

    return pretty_url
