import subprocess
import os


# ТВОЙ ПУТЬ К MERMAID CLI
MMDC_PATH = r"C:\Users\meps7\AppData\Roaming\npm\mmdc.cmd"

# Папка для PNG диаграмм
DIAGRAMS_DIR = os.path.join(os.path.dirname(__file__), "diagrams")
os.makedirs(DIAGRAMS_DIR, exist_ok=True)


def render_diagram_png(mermaid_code: str, name: str) -> str:
    """
    Генерация PNG диаграммы Mermaid → PNG.
    Путь к mmdc.cmd фиксированный, чтобы избежать WinError 2.
    """

    # проверка
    if not os.path.exists(MMDC_PATH):
        print(f"[Mermaid ERROR] mmdc not found at: {MMDC_PATH}")
        return None

    # файлы
    mmd_path = os.path.join(DIAGRAMS_DIR, f"{name}.mmd")
    png_path = os.path.join(DIAGRAMS_DIR, f"{name}.png")

    # записываем файл .mmd
    with open(mmd_path, "w", encoding="utf-8") as f:
        f.write(mermaid_code)

    # команда рендера
    cmd = [
        MMDC_PATH,
        "-i", mmd_path,
        "-o", png_path,
        "-t", "default",
        "-b", "transparent",
        "-w", "1400"
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"[Mermaid OK] Generated: {png_path}")
    except Exception as e:
        print(f"[Mermaid ERROR] {e}")
        return None

    return png_path
