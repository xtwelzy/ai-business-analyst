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
# Генерация короткого title + URL-safe
# =====================================================================================
def make_safe_title(raw: str):
    if not raw:
        return "New Project", "New-Project"

    words = raw.split()
    short = " ".join(words[:5])

    for bad in [":", "/", "\\", "|", "*", "?", "\"", "<", ">"]:
        short = short.replace(bad, "")

    safe_url = short.replace(" ", "-")
    return short, safe_url


# =====================================================================================
# Поиск страницы по названию
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
# UPDATE PAGE
# =====================================================================================
def update_page(page_id, title, html, version):
    payload = {
        "id": page_id,
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "version": {"number": version},
        "body": {"storage": {"value": html, "representation": "storage"}}
    }

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}"
    resp = requests.put(url, json=payload, auth=auth)

    if resp.status_code not in (200, 201):
        print("[Confluence] Update error:", resp.text)
        return None

    return page_id


# =====================================================================================
# CREATE PAGE
# =====================================================================================
def create_page(title, html):
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": CONFLUENCE_SPACE_KEY},
        "body": {"storage": {"value": html, "representation": "storage"}}
    }

    url = f"{CONFLUENCE_BASE_URL}/rest/api/content"
    resp = requests.post(url, json=payload, auth=auth)

    if resp.status_code not in (200, 201):
        print("[Confluence] Create error:", resp.text)
        return None

    return resp.json()["id"]


# =====================================================================================
# UPLOAD / UPDATE ATTACHMENT
# =====================================================================================
def upload_or_update_attachment(page_id, file_path):
    filename = os.path.basename(file_path)

    # Проверяем, есть ли уже вложение
    url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/attachment"
    resp = requests.get(url, auth=auth)

    existing_id = None
    if resp.status_code == 200:
        for att in resp.json().get("results", []):
            if att["title"] == filename:
                existing_id = att["id"]
                break

    # Если есть — обновляем
    if existing_id:
        upload_url = f"{CONFLUENCE_BASE_URL}/rest/api/content/{page_id}/child/attachment/{existing_id}/data"
    else:
        upload_url = url

    headers = {"X-Atlassian-Token": "no-check"}
    files = {"file": (filename, open(file_path, "rb"))}

    resp = requests.post(upload_url, files=files, headers=headers, auth=auth)

    if resp.status_code not in (200, 201):
        print("[Confluence] Attachment upload error:", resp.text)
        return None

    return filename

def convert_markdown_tables(text):
    import re

    # Находим все части, которые похожи на таблицы
    pattern = r"(?:^\|.*\|\s*$\n?)+"
    blocks = re.findall(pattern, text, flags=re.MULTILINE)

    html = text

    for block in blocks:
        lines = block.strip().split("\n")

        # Отфильтруем лишние пустые строки
        lines = [ln for ln in lines if ln.strip()]

        # Найдём строки с '---' (разделитель заголовков)
        divider_index = None
        for i, ln in enumerate(lines):
            if re.match(r"^\|[-: ]+\|", ln):
                divider_index = i
                break

        if divider_index is None:
            continue  # это не таблица

        header_line = lines[0]
        header_cols = [c.strip() for c in header_line.strip("|").split("|")]

        # Строки после разделителя — тело таблицы
        body_lines = lines[divider_index + 1:]

        rows = []
        for ln in body_lines:
            # Если строка разорвана GPT переносом — склеиваем
            if ln.count("|") < len(header_cols) + 1:
                # недостающая строка — присоединяем к предыдущей
                if rows:
                    rows[-1][-1] += " " + ln.strip()
                continue

            cols = [c.strip() for c in ln.strip("|").split("|")]
            rows.append(cols)

        # Сборка HTML
        html_table = "<table><thead><tr>"
        for h in header_cols:
            html_table += f"<th>{h}</th>"
        html_table += "</tr></thead><tbody>"

        for row in rows:
            html_table += "<tr>"
            for col in row:
                html_table += f"<td>{col}</td>"
            html_table += "</tr>"

        html_table += "</tbody></table>"

        # Заменяем markdown таблицу на HTML
        html = html.replace(block, html_table)

    return html



# =====================================================================================
# CREATE BRD PAGE
# =====================================================================================
def create_brd_page(title_raw: str, brd_text: str, pdf_path: str, diagrams: dict):

    short_title, safe_url = make_safe_title(title_raw)
    title = f"BRD – {short_title}"

    # ------------------------ STEP 1: CREATE BASE PAGE ------------------------
    base_html = f"""
    <h1>{title}</h1>
    <p>Автоматически сгенерированный BRD документ.</p>
    <p><b>PDF и диаграммы будут добавлены во вложения.</b></p>
    <h2>BRD Текст</h2>
    {convert_markdown_tables(brd_text)}
    <h2>Диаграммы</h2>
    <p>Загрузка…</p>
    """

    existing = find_page_by_title(title)

    if existing:
        page_id = existing["id"]
        version = existing["version"]["number"] + 1
        update_page(page_id, title, base_html, version)
    else:
        page_id = create_page(title, base_html)
        version = 1

    if not page_id:
        return None

    # ------------------------ STEP 2: UPLOAD ATTACHMENTS ------------------------
    upload_or_update_attachment(page_id, pdf_path)

    attachments = {}
    for name, file_path in diagrams.items():
        filename = upload_or_update_attachment(page_id, file_path)
        if filename:
            attachments[name] = filename

    # ------------------------ STEP 3: BUILD FINAL HTML WITH IMAGES ------------------------
    images_html = ""
    for name, filename in attachments.items():
        images_html += f"""
        <h3>{name}</h3>
        <ac:image>
            <ri:attachment ri:filename="{filename}" />
        </ac:image>
        <br/><br/>
        """

    final_html = f"""
    <h1>{title}</h1>
    <p>Автоматически сгенерированный BRD документ.</p>
    <p><b>PDF и диаграммы доступны во вложениях.</b></p>
    <h2>BRD Текст</h2>
    {convert_markdown_tables(brd_text)}
    <h2>Диаграммы</h2>
    {images_html}
    """

    # ------------------------ STEP 4: FINAL UPDATE ------------------------
    latest = find_page_by_title(title)
    version = latest["version"]["number"] + 1
    update_page(page_id, title, final_html, version)

    return f"{CONFLUENCE_BASE_URL}/spaces/{CONFLUENCE_SPACE_KEY}/pages/{page_id}/{safe_url}"
