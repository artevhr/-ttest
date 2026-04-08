"""
content_loader.py

Каждый файл в content/ — самостоятельный JSON.
Бот автоматически подхватывает все файлы из папок.

══════════════════════════════════════════════════════════════
ФОРМАТЫ ФАЙЛОВ (присылай мне оригинал — я верну готовый JSON)
══════════════════════════════════════════════════════════════

────────────────────────────────────────────────────────────
📚 СБОРНИК  →  content/collections/<предмет>/<имя>.json
────────────────────────────────────────────────────────────
{
  "id":      "math_col_2024",
  "title":   "Сборник задач по математике 2024",
  "subject": "math",
  "pages": [
    {
      "title":   "Тема 1. Квадратные уравнения",
      "content": "Полный текст страницы/раздела..."
    },
    {
      "title":   "Тема 2. Прогрессии",
      "content": "..."
    }
  ]
}

────────────────────────────────────────────────────────────
✏️ ТЕСТ  →  content/tests/<тип>/<предмет>_<тип>_<год>_<этап>_<вариант>.json
────────────────────────────────────────────────────────────
Имя файла:
  math_drt_2025-2026_I_1.json
  russian_rt_2024_II_2.json
  english_ct_2024_1.json         ← без этапа (для ЦТ/доп)

{
  "title": "ДРТ по математике 2025-2026, I этап, вариант 1",
  "questions": [
    {
      "id": 1,
      "text": "Вычислите: (−3)² − 4·2",
      "type": "choice",
      "options": {"A": "1", "B": "17", "C": "−8", "D": "−1"},
      "correct": "A",
      "explanation": "Пошаговое объяснение:\n(−3)² = 9\n4·2 = 8\n9 − 8 = 1",
      "primary_points": 1
    },
    {
      "id": 2,
      "text": "Решите уравнение: x² − 5x + 6 = 0\nВведи корни через запятую.",
      "type": "input",
      "correct": ["2, 3", "2,3", "x=2, x=3"],
      "explanation": "D = b²−4ac = 25−24 = 1\nx = (5±1)/2\nx₁=2, x₂=3",
      "primary_points": 2
    }
  ],
  "scoring_table": {
    "0":0, "1":10, "2":20, "3":30
  }
}

────────────────────────────────────────────────────────────
📖 СОКРАЩЁННЫЙ СБОРНИК  →  content/short_collections/<предмет>/<имя>.json
────────────────────────────────────────────────────────────
{
  "id":      "quadratic",
  "title":   "📐 Квадратные уравнения",
  "subject": "math",
  "pages": [
    {"title": "Что это", "content": "ax²+bx+c=0, где a≠0..."},
    {"title": "Дискриминант", "content": "D = b²−4ac\n..."}
  ]
}

────────────────────────────────────────────────────────────
📌 ШПАРГАЛКА  →  content/cheatsheets/<предмет>/<имя>.json
────────────────────────────────────────────────────────────
{
  "id":      "math_cheat_fsm",
  "title":   "Формулы сокращённого умножения",
  "subject": "math",
  "pages": [
    {"title": "Квадрат суммы/разности", "content": "(a+b)²=a²+2ab+b²\n(a−b)²=a²−2ab+b²"},
    {"title": "Разность квадратов",     "content": "a²−b²=(a+b)(a−b)"}
  ]
}
"""

import json, os
from config import CONTENT_DIR


def _load(path: str):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _list_json(folder: str) -> list:
    if not os.path.isdir(folder):
        return []
    return sorted(f for f in os.listdir(folder) if f.endswith(".json"))


# ──────────────────────────── СБОРНИКИ ──────────────────────────────

def get_collections(subject: str) -> list:
    folder = f"{CONTENT_DIR}/collections/{subject}"
    result = []
    for fname in _list_json(folder):
        data = _load(f"{folder}/{fname}")
        if data and "title" in data and "pages" in data:
            data.setdefault("id", fname[:-5])
            result.append({"id": data["id"], "title": data["title"]})
    return result


def get_collection(subject: str, col_id: str):
    folder = f"{CONTENT_DIR}/collections/{subject}"
    for fname in _list_json(folder):
        data = _load(f"{folder}/{fname}")
        if data and data.get("id", fname[:-5]) == col_id:
            return data
    return None


# ──────────────────────────── ТЕСТЫ ─────────────────────────────────

def _parse_test_filename(fname: str):
    name  = fname[:-5]
    parts = name.split("_")
    if len(parts) < 4:
        return None
    subject = parts[0]
    ttype   = parts[1]
    year    = parts[2]
    roman   = {"I", "II", "III"}
    if len(parts) >= 5 and parts[3] in roman:
        stage, variant = parts[3], parts[4] if len(parts) > 4 else "1"
    else:
        stage, variant = None, parts[3]
    return dict(subject=subject, ttype=ttype, year=year, stage=stage, variant=variant)


def get_test_years(subject: str, ttype: str) -> list:
    years = set()
    for fname in _list_json(f"{CONTENT_DIR}/tests/{ttype}"):
        p = _parse_test_filename(fname)
        if p and p["subject"] == subject and p["ttype"] == ttype:
            years.add(p["year"])
    return sorted(years, reverse=True)


def get_test_stages(subject: str, ttype: str, year: str) -> list:
    stages = set()
    for fname in _list_json(f"{CONTENT_DIR}/tests/{ttype}"):
        p = _parse_test_filename(fname)
        if p and p["subject"] == subject and p["ttype"] == ttype and p["year"] == year:
            stages.add(p["stage"] or "—")
    order = {"I": 0, "II": 1, "III": 2, "—": 3}
    return sorted(stages, key=lambda s: order.get(s, 99))


def get_test_variants(subject: str, ttype: str, year: str, stage: str) -> list:
    variants, ns = set(), None if stage == "—" else stage
    for fname in _list_json(f"{CONTENT_DIR}/tests/{ttype}"):
        p = _parse_test_filename(fname)
        if p and p["subject"]==subject and p["ttype"]==ttype and p["year"]==year and p["stage"]==ns:
            variants.add(p["variant"])
    return sorted(variants)


def get_test(subject, ttype, year, stage, variant):
    ns = None if stage == "—" else stage
    for fname in _list_json(f"{CONTENT_DIR}/tests/{ttype}"):
        p = _parse_test_filename(fname)
        if p and p["subject"]==subject and p["ttype"]==ttype and p["year"]==year \
                and p["stage"]==ns and p["variant"]==variant:
            return _load(f"{CONTENT_DIR}/tests/{ttype}/{fname}")
    return None


# ──────────────────────── СОКРАЩЁННЫЕ СБОРНИКИ ──────────────────────

def get_short_topics(subject: str) -> list:
    folder = f"{CONTENT_DIR}/short_collections/{subject}"
    result = []
    for fname in _list_json(folder):
        data = _load(f"{folder}/{fname}")
        if data and "title" in data and "pages" in data:
            data.setdefault("id", fname[:-5])
            result.append({"id": data["id"], "title": data["title"]})
    return result


def get_short_topic(subject: str, topic_id: str):
    folder = f"{CONTENT_DIR}/short_collections/{subject}"
    for fname in _list_json(folder):
        data = _load(f"{folder}/{fname}")
        if data and data.get("id", fname[:-5]) == topic_id:
            return data
    return None


# ──────────────────────────── ШПАРГАЛКИ ─────────────────────────────

def get_cheatsheets(subject: str) -> list:
    folder = f"{CONTENT_DIR}/cheatsheets/{subject}"
    result = []
    for fname in _list_json(folder):
        data = _load(f"{folder}/{fname}")
        if data and "title" in data and "pages" in data:
            data.setdefault("id", fname[:-5])
            result.append({"id": data["id"], "title": data["title"]})
    return result


def get_cheatsheet(subject: str, cheat_id: str):
    folder = f"{CONTENT_DIR}/cheatsheets/{subject}"
    for fname in _list_json(folder):
        data = _load(f"{folder}/{fname}")
        if data and data.get("id", fname[:-5]) == cheat_id:
            return data
    return None


# ──────────────────────────── БАЛЛЫ ─────────────────────────────────

def calc_scores(test: dict, answers: dict) -> dict:
    primary = max_primary = 0
    details = []
    for idx, q in enumerate(test["questions"]):
        pts = q.get("primary_points", 1)
        max_primary += pts
        user_ans = answers.get(idx)
        correct  = q["correct"]
        if q["type"] == "choice":
            is_correct = str(user_ans or "").upper() == str(correct).upper()
        else:
            if isinstance(correct, list):
                is_correct = any(str(user_ans or "").strip().lower() == str(c).strip().lower() for c in correct)
            else:
                is_correct = str(user_ans or "").strip().lower() == str(correct).strip().lower()
        earned = pts if is_correct else 0
        primary += earned
        details.append(dict(q_idx=idx+1, correct=correct, user_ans=user_ans,
                            is_correct=is_correct, points=earned,
                            explanation=q.get("explanation", "")))
    test_score = test.get("scoring_table", {}).get(str(primary), 0)
    return dict(primary=primary, max_primary=max_primary,
                test_score=test_score, details=details)
