import json
import os
from config import DATA_PATH


def load_state():
    if not os.path.exists(DATA_PATH):
        return {}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_state(state):
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)


def add_user_answer(user_id: str, key: str, value: str):
    state = load_state()
    if user_id not in state:
        state[user_id] = {}

    state[user_id][key] = value
    save_state(state)


def get_user_dialog(user_id: str):
    state = load_state()
    return state.get(user_id, {})


def reset_user(user_id: str):
    state = load_state()
    if user_id in state:
        del state[user_id]
    save_state(state)
