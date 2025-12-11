# controllers.py
from models import DBModel
import views
from typing import Dict, Any


class Controller:
    def __init__(self):
        self.model = DBModel()

        # Нові таблиці твоєї бази:
        self.tables = [
            "supplier",
            "product",
            "supply",
            "inventory",
        ]

    def close(self):
        self.model.close()

    def run(self):
        views.print_banner()
        while True:
            views.show_menu()
            choice = views.prompt("Виберіть опцію")
            if choice == "1":
                self.action_list_tables()
            elif choice == "2":
                self.action_show_table()
            elif choice == "3":
                self.action_show_by_pk()
            elif choice == "4":
                self.action_insert()
            elif choice == "5":
                self.action_update()
            elif choice == "6":
                self.action_delete()
            elif choice == "7":
                self.action_generate()
            elif choice == "8":
                self.action_complex_queries()
            elif choice == "9":
                self.action_demo_check_children()
            elif choice == "0":
                print("До побачення!")
                break
            else:
                print("Невірний вибір. Спробуйте ще.")

    # ---------------------------------------------------------
    # 1. Список таблиць
    # ---------------------------------------------------------
    def action_list_tables(self):
        try:
            tables = self.model.list_tables()
            views.print_tables(tables)
        except Exception as e:
            views.show_error(str(e))

    # ---------------------------------------------------------
    # 2. Показати таблицю
    # ---------------------------------------------------------
    def action_show_table(self):
        table = views.prompt("Назва таблиці")
        if table not in self.tables:
            views.show_error("Невідома таблиця. Приклад: supplier")
            return
        try:
            rows = self.model.select_all(table, limit=500)
            views.print_rows(rows)
        except Exception as e:
            views.show_error("Не вдалося отримати записи.")

    # ---------------------------------------------------------
    # 3. Отримати запис за PK
    # ---------------------------------------------------------
    def action_show_by_pk(self):
        table = views.prompt("Назва таблиці")
        if table not in self.tables:
            views.show_error("Невідома таблиця")
            return

        pk = self.model.primary_key(table)
        if not pk:
            views.show_error("PK не знайдено")
            return

        val = views.prompt(f"Значення PK ({pk})")

        # автоматичне визначення типу PK
        col_info = next((c for c in self.model.columns_info(table) if c['name'] == pk), None)
        if col_info and "int" in col_info["type"]:
            try:
                val = int(val)
            except:
                views.show_error("PK має бути числом")
                return

        try:
            row = self.model.select_by_pk(table, pk, val)
            views.print_row(row)
        except:
            views.show_error("Помилка при отриманні")

    # ---------------------------------------------------------
    # Універсальний ввід+валідація
    # ---------------------------------------------------------
    def _input_and_validate_for_table(self, table: str, skip_pk=True) -> Dict[str, Any]:
        cols = self.model.columns_info(table)
        pk = self.model.primary_key(table)
        data = {}

        for c in cols:
            name = c["name"]
            dtype = c["type"]

            if skip_pk and name == pk:
                continue

            raw = views.prompt_nullable(f"{name} ({dtype})")

            if raw is None:
                if not c["nullable"]:
                    views.show_error(f"Поле {name} не може бути пустим.")
                    return self._input_and_validate_for_table(table, skip_pk)
                data[name] = None
                continue

            # --- типи ---
            if "int" in dtype:
                try:
                    data[name] = int(raw)
                except:
                    views.show_error(f"{name} очікується integer")
                    return self._input_and_validate_for_table(table, skip_pk)
            elif dtype in ("numeric", "real", "double precision", "decimal"):
                try:
                    data[name] = float(raw)
                except:
                    views.show_error(f"{name} очікується число")
                    return self._input_and_validate_for_table(table, skip_pk)
            elif dtype == "date":
                parsed = self.model.parse_date(raw)
                if not parsed:
                    views.show_error(f"Невірний формат дати {name}")
                    return self._input_and_validate_for_table(table, skip_pk)
                data[name] = parsed
            else:
                data[name] = raw

        return data

    # ---------------------------------------------------------
    # 4. INSERT
    # ---------------------------------------------------------
    def action_insert(self):
        table = views.prompt("Назва таблиці")
        if table not in self.tables:
            views.show_error("Невідома таблиця")
            return

        data = self._input_and_validate_for_table(table)

        # Перевірка FK для supply і inventory
        if table == "supply":
            checks = [
                ("supplier", "supplier_id"),
                ("product", "product_id"),
            ]
        elif table == "inventory":
            checks = [
                ("product", "product_id"),
            ]
        else:
            checks = []

        for parent_table, col in checks:
            val = data.get(col)
            if val is None or not self.model.parent_exists(parent_table, col, val):
                views.show_error(f"{col}={val} не існує у {parent_table}")
                return

        success, err = self.model.insert(table, data)
        if success:
            views.show_success("Запис додано.")
        else:
            views.show_error(f"Помилка: {err}")

    # ---------------------------------------------------------
    # 5. UPDATE
    # ---------------------------------------------------------
    def action_update(self):
        table = views.prompt("Назва таблиці")
        if table not in self.tables:
            views.show_error("Невідома таблиця")
            return

        pk = self.model.primary_key(table)
        pk_raw = views.prompt(f"PK ({pk})")

        col_info = next((c for c in self.model.columns_info(table) if c["name"] == pk), None)
        if col_info and "int" in col_info["type"]:
            try:
                pk_val = int(pk_raw)
            except:
                views.show_error("PK має бути числом")
                return
        else:
            pk_val = pk_raw

        row = self.model.select_by_pk(table, pk, pk_val)
        if not row:
            views.show_error("Рядок не знайдено")
            return

        updates = {}
        for c in self.model.columns_info(table):
            if c["name"] == pk:
                continue
            raw = views.prompt_nullable(f"{c['name']} (поточне: {row[c['name']]})")
            if raw is None:
                continue
            updates[c["name"]] = raw

        if not updates:
            views.show_message("Нічого не змінено.")
            return

        success, err = self.model.update(table, pk, pk_val, updates)
        if success:
            views.show_success("Оновлено.")
        else:
            views.show_error(f"Помилка: {err}")

    # ---------------------------------------------------------
    # 6. DELETE
    # ---------------------------------------------------------
    def action_delete(self):
        table = views.prompt("Назва таблиці")
        if table not in self.tables:
            views.show_error("Невідома таблиця")
            return

        pk = self.model.primary_key(table)
        pk_raw = views.prompt(f"PK ({pk})")

        pk_col = next((c for c in self.model.columns_info(table) if c["name"] == pk), None)
        if pk_col and "int" in pk_col["type"]:
            try:
                pk_val = int(pk_raw)
            except:
                views.show_error("PK має бути числом")
                return
        else:
            pk_val = pk_raw

        try:
            if self.model.has_child_rows(table, pk, pk_val):
                views.show_error("Не можна видалити — є дочірні записи.")
                return
        except:
            views.show_error("Не вдалося перевірити залежності.")
            return

        if views.prompt("Підтвердити (так/ні)?").lower() not in ("так", "y", "yes"):
            views.show_message("Скасовано.")
            return

        success, err = self.model.delete(table, pk, pk_val)
        if success:
            views.show_success("Видалено.")
        else:
            views.show_error(f"Не вдалося: {err}")

    # ---------------------------------------------------------
    # 7. Генерація даних
    # ---------------------------------------------------------
    def action_generate(self):
        count_raw = views.prompt("Скільки записів генерувати?")
        try:
            count = int(count_raw)
        except:
            views.show_error("Потрібно число.")
            return

        tasks = [
            ("supplier", self.model.generate_suppliers),
            ("product", self.model.generate_products),
            ("supply", self.model.generate_supplies),
            ("inventory", self.model.generate_inventory),
        ]

        for name, func in tasks:
            ok, err = func(count)
            if ok:
                views.show_success(f"{name}: згенеровано {count}")
            else:
                views.show_error(f"{name}: помилка — {err}")

    # ---------------------------------------------------------
    # 8. Складні SQL запити
    # ---------------------------------------------------------
    def action_complex_queries(self):
        views.show_message("1) Загальна сума постачань по постачальниках")
        views.show_message("2) Товари нижче мінімального запасу")
        views.show_message("3) Найдорожчі категорії постачань")
        views.show_message("4) ТОП-10 товарів за обсягом постачань")
        views.show_message("5) Постачання за останні 30 днів")

        choice = views.prompt("Виберіть запит (1-5)")

        query_map = {
            "1": self.model.query_supplier_totals,
            "2": self.model.query_products_below_min_stock,
            "3": self.model.query_category_supply_costs,
            "4": self.model.query_top_products_by_supply_volume,
            "5": self.model.query_last_month_supplies,
        }

        func = query_map.get(choice)
        if not func:
            views.show_error("Невірний вибір")
            return

        rows, time_ms, explain, err = func()
        if err:
            views.show_error(err)
            return

        views.show_query_result(rows, time_ms, explain)

    # ---------------------------------------------------------
    # 9. Перевірка залежностей
    # ---------------------------------------------------------
    def action_demo_check_children(self):
        table = views.prompt("Назва таблиці")
        if table not in self.tables:
            views.show_error("Невідома таблиця")
            return

        pk = self.model.primary_key(table)
        val = views.prompt(f"PK ({pk})")

        try:
            has = self.model.has_child_rows(table, pk, val)
        except:
            views.show_error("Помилка перевірки.")
            return

        if has:
            views.show_message("Є дочірні записи.")
        else:
            views.show_message("Немає дочірніх записів.")
