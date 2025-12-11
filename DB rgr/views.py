# views.py
from typing import List, Dict, Any, Optional

def print_banner():
    print("===================================")
    print("   Система обліку постачань склад")
    print("===================================\n")

def show_menu():
    print("\nМеню:")
    print("1. Список таблиць")
    print("2. Показати таблицю")
    print("3. Показати запис за PK")
    print("4. Додати запис")
    print("5. Оновити запис")
    print("6. Видалити запис")
    print("7. Генерація випадкових даних")
    print("8. Складні SQL запити")
    print("9. Перевірка дочірніх записів")
    print("0. Вийти")

def prompt(msg: str) -> str:
    return input(f"{msg}: ").strip()

def prompt_nullable(msg: str) -> Optional[str]:
    raw = input(f"{msg} (залиште пустим для NULL): ").strip()
    return raw if raw != "" else None

def print_tables(tables: List[str]):
    print("\nТаблиці бази:")
    for t in tables:
        print(" -", t)

def print_rows(rows: List[Dict[str, Any]]):
    if not rows:
        print("Немає записів.")
        return
    print("\nРядки таблиці:")
    for r in rows:
        print(r)

def print_row(row: Optional[Dict[str, Any]]):
    if not row:
        print("Запис не знайдено.")
    else:
        print("\nЗапис:")
        print(row)

def show_error(msg: str):
    print(f"[ПОМИЛКА] {msg}")

def show_success(msg: str):
    print(f"[УСПІХ] {msg}")

def show_message(msg: str):
    print(f"[INFO] {msg}")

def show_query_result(rows: List[Dict[str, Any]], exec_time_ms: Optional[float], explain: str):
    print("\n=== Результат запиту ===")
    for r in rows:
        print(r)
    if exec_time_ms is not None:
        print(f"\nЧас виконання: {exec_time_ms:.2f} ms")
    if explain:
        print("\n--- EXPLAIN ANALYZE ---")
        print(explain)
