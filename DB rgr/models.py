# models.py
from typing import List, Dict, Any, Optional, Tuple
import psycopg2
import psycopg2.extras
from psycopg2 import sql
from config import DB
from dateutil import parser as date_parser
import random
from datetime import datetime, timedelta


class DBModel:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(**DB)
            self.conn.autocommit = True
        except Exception as e:
            raise RuntimeError("Не вдалося підключитися до бази даних. Перевірте налаштування в config.py") from e

    def close(self):
        self.conn.close()

    # ----------------- Generic CRUD -----------------
    def list_tables(self) -> List[str]:
        q = """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema='public' AND table_type='BASE TABLE'
        ORDER BY table_name;
        """
        with self.conn.cursor() as cur:
            cur.execute(q)
            return [r[0] for r in cur.fetchall()]

    def columns_info(self, table: str) -> List[Dict[str, Any]]:
        q = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name=%s
        ORDER BY ordinal_position;
        """
        with self.conn.cursor() as cur:
            cur.execute(q, (table,))
            res = []
            for r in cur.fetchall():
                res.append({"name": r[0], "type": r[1], "nullable": (r[2] == 'YES')})
            return res

    def primary_key(self, table: str) -> Optional[str]:
        q = """
        SELECT a.attname
        FROM pg_index i
        JOIN pg_attribute a ON a.attrelid = i.indrelid AND a.attnum = ANY(i.indkey)
        WHERE i.indrelid = quote_ident(%s)::regclass AND i.indisprimary;
        """
        with self.conn.cursor() as cur:
            cur.execute(q, (table,))
            row = cur.fetchone()
            return row[0] if row else None

    def select_all(self, table: str, limit: int = 200) -> List[Dict[str, Any]]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql.SQL('SELECT * FROM {} ORDER BY 1 LIMIT %s').format(sql.Identifier(table)), (limit,))
            return cur.fetchall()

    def select_by_pk(self, table: str, pk: str, pk_value: Any) -> Optional[Dict[str, Any]]:
        with self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql.SQL('SELECT * FROM {} WHERE {}=%s').format(sql.Identifier(table), sql.Identifier(pk)), (pk_value,))
            return cur.fetchone()

    def insert(self, table: str, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        cols = list(data.keys())
        vals = [data[c] for c in cols]
        query = sql.SQL('INSERT INTO {} ({}) VALUES ({})').format(
            sql.Identifier(table),
            sql.SQL(', ').join(map(sql.Identifier, cols)),
            sql.SQL(', ').join(sql.Placeholder() * len(cols))
        )
        with self.conn.cursor() as cur:
            try:
                cur.execute(query, vals)
                return True, None
            except psycopg2.Error as e:
                return False, e.pgerror or str(e)

    def update(self, table: str, pk: str, pk_value: Any, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        cols = list(data.keys())
        vals = [data[c] for c in cols] + [pk_value]
        set_clause = sql.SQL(', ').join(
            sql.Composed([sql.Identifier(c), sql.SQL(' = '), sql.Placeholder()]) for c in cols
        )
        query = sql.SQL('UPDATE {} SET {} WHERE {} = %s').format(
            sql.Identifier(table),
            set_clause,
            sql.Identifier(pk)
        )
        with self.conn.cursor() as cur:
            try:
                cur.execute(query, vals)
                return True, None
            except psycopg2.Error as e:
                return False, e.pgerror or str(e)

    def delete(self, table: str, pk: str, pk_value: Any) -> Tuple[bool, Optional[str]]:
        query = sql.SQL('DELETE FROM {} WHERE {} = %s').format(sql.Identifier(table), sql.Identifier(pk))
        with self.conn.cursor() as cur:
            try:
                cur.execute(query, (pk_value,))
                return True, None
            except psycopg2.Error as e:
                return False, e.pgerror or str(e)

    # ----------------- Helpers -----------------
    def has_child_rows(self, parent_table: str, parent_pk: str, pk_value: Any) -> bool:
        q = """
        SELECT c.table_name, kcu.column_name
        FROM information_schema.table_constraints c
        JOIN information_schema.key_column_usage kcu
          ON c.constraint_name = kcu.constraint_name AND c.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage ccu
          ON c.constraint_name = ccu.constraint_name AND c.table_schema = ccu.constraint_schema
        WHERE c.constraint_type = 'FOREIGN KEY' AND ccu.table_name = %s AND ccu.column_name = %s;
        """
        with self.conn.cursor() as cur:
            cur.execute(q, (parent_table, parent_pk))
            fks = cur.fetchall()
            for fk_table, fk_col in fks:
                check_q = sql.SQL('SELECT EXISTS (SELECT 1 FROM {} WHERE {} = %s LIMIT 1)').format(
                    sql.Identifier(fk_table), sql.Identifier(fk_col)
                )
                cur.execute(check_q, (pk_value,))
                if cur.fetchone()[0]:
                    return True
        return False

    def parent_exists(self, parent_table: str, parent_pk: str, pk_value: Any) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(sql.SQL('SELECT EXISTS (SELECT 1 FROM {} WHERE {} = %s LIMIT 1)').format(
                sql.Identifier(parent_table), sql.Identifier(parent_pk)
            ), (pk_value,))
            return cur.fetchone()[0]

    def parse_date(self, value: str) -> Optional[str]:
        try:
            d = date_parser.parse(value)
            return d.date().isoformat()
        except Exception:
            return None

    # ----------------- Генерація даних -----------------
    def generate_suppliers(self, count: int) -> Tuple[bool, Optional[str]]:
        first_names = ["Іван", "Петро", "Ольга", "Марія", "Андрій"]
        last_names = ["Іванов", "Петренко", "Сидоренко", "Коваленко", "Бондаренко"]
        domains = ["example.ua", "mail.ua", "suppliers.ua"]
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT COALESCE(MAX(supplier_id),0)+1 FROM supplier")
                start_id = cur.fetchone()[0]
                for i in range(count):
                    supplier_id = start_id + i
                    company_name = f"Компанія {supplier_id}"
                    contact_person = f"{random.choice(first_names)} {random.choice(last_names)}"
                    phone = f"+380{random.randint(500000000, 999999999)}"
                    email = f"user{supplier_id}@{random.choice(domains)}"
                    cur.execute("""
                        INSERT INTO supplier(supplier_id, company_name, contact_person, phone, email)
                        VALUES (%s,%s,%s,%s,%s)
                    """, (supplier_id, company_name, contact_person, phone, email))
                return True, None
            except psycopg2.Error as e:
                return False, e.pgerror or str(e)

    def generate_products(self, count: int) -> Tuple[bool, Optional[str]]:
        units = ["шт", "уп", "кг", "л"]
        categories = ["Комп'ютерна техніка", "Оргтехніка", "Канцтовари", "Витратні матеріали"]
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT COALESCE(MAX(product_id),0)+1 FROM product")
                start_id = cur.fetchone()[0]
                for i in range(count):
                    product_id = start_id + i
                    product_name = f"Товар {product_id}"
                    unit_measure = random.choice(units)
                    min_stock = random.randint(1, 100)
                    category = random.choice(categories)
                    cur.execute("""
                        INSERT INTO product(product_id, product_name, unit_measure, min_stock, category)
                        VALUES (%s,%s,%s,%s,%s)
                    """, (product_id, product_name, unit_measure, min_stock, category))
                return True, None
            except psycopg2.Error as e:
                return False, e.pgerror or str(e)

    def generate_supplies(self, count: int) -> Tuple[bool, Optional[str]]:
        with self.conn.cursor() as cur:
            try:
                # FK: get existing supplier_ids and product_ids
                cur.execute("SELECT supplier_id FROM supplier")
                supplier_ids = [r[0] for r in cur.fetchall()]
                cur.execute("SELECT product_id FROM product")
                product_ids = [r[0] for r in cur.fetchall()]
                if not supplier_ids or not product_ids:
                    return False, "Відсутні дані для FK"

                cur.execute("SELECT COALESCE(MAX(supply_id),0)+1 FROM supply")
                start_id = cur.fetchone()[0]

                for i in range(count):
                    supply_id = start_id + i
                    supplier_id = random.choice(supplier_ids)
                    product_id = random.choice(product_ids)
                    supply_date = datetime.now() - timedelta(days=random.randint(0, 365))
                    document_number = f"ПН-{supply_id:05d}"
                    quantity = round(random.uniform(1, 100), 2)
                    unit_price = round(random.uniform(10, 5000), 2)
                    cur.execute("""
                        INSERT INTO supply(supply_id, supplier_id, product_id, supply_date, document_number, quantity, unit_price)
                        VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """, (supply_id, supplier_id, product_id, supply_date, document_number, quantity, unit_price))
                return True, None
            except psycopg2.Error as e:
                return False, e.pgerror or str(e)

    def generate_inventory(self, count: int) -> Tuple[bool, Optional[str]]:
        locations = [
            "Секція A, полиця 1", "Секція A, полиця 2", "Секція A, полиця 3",
            "Секція B, полиця 1", "Секція B, полиця 2", "Секція B, полиця 3",
            "Секція C, полиця 1", "Секція C, полиця 2", "Секція C, полиця 3",
            "Секція D, полиця 1", "Секція D, полиця 2"
        ]
        with self.conn.cursor() as cur:
            try:
                cur.execute("SELECT COALESCE(MAX(inventory_id),0)+1 FROM inventory")
                start_id = cur.fetchone()[0]
                cur.execute("SELECT product_id FROM product")
                product_ids = [r[0] for r in cur.fetchall()]
                if not product_ids:
                    return False, "Відсутні продукти для FK"

                used_products = set()
                for i in range(count):
                    inventory_id = start_id + i
                    product_id = random.choice(product_ids)
                    # не дублюємо inventory для одного product_id
                    while product_id in used_products:
                        product_id = random.choice(product_ids)
                    used_products.add(product_id)
                    quantity = round(random.uniform(0, 200), 2)
                    last_updated = datetime.now() - timedelta(days=random.randint(0, 365))
                    location = random.choice(locations)
                    cur.execute("""
                        INSERT INTO inventory(inventory_id, product_id, quantity, last_updated, location)
                        VALUES (%s,%s,%s,%s,%s)
                    """, (inventory_id, product_id, quantity, last_updated, location))
                return True, None
            except psycopg2.Error as e:
                return False, e.pgerror or str(e)
