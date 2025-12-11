BEGIN;

-- Таблиця 1: Постачальники (Supplier)
CREATE TABLE IF NOT EXISTS public.supplier
(
    supplier_id INTEGER NOT NULL,
    company_name CHARACTER VARYING(100) COLLATE pg_catalog."default" NOT NULL,
    contact_person CHARACTER VARYING(100) COLLATE pg_catalog."default",
    phone CHARACTER VARYING(20) COLLATE pg_catalog."default",
    email CHARACTER VARYING(100) COLLATE pg_catalog."default",
    CONSTRAINT supplier_pkey PRIMARY KEY (supplier_id),
    CONSTRAINT supplier_company_name_unique UNIQUE (company_name),
    CONSTRAINT supplier_email_unique UNIQUE (email)
);

COMMENT ON TABLE public.supplier IS 'Таблиця постачальників товарів';
COMMENT ON COLUMN public.supplier.supplier_id IS 'Унікальний ідентифікатор постачальника';
COMMENT ON COLUMN public.supplier.company_name IS 'Назва компанії постачальника';
COMMENT ON COLUMN public.supplier.contact_person IS 'ПІБ контактної особи';
COMMENT ON COLUMN public.supplier.phone IS 'Контактний телефон';
COMMENT ON COLUMN public.supplier.email IS 'Електронна адреса для звязку';

-- Таблиця 2: Товари (Product)
CREATE TABLE IF NOT EXISTS public.product
(
    product_id INTEGER NOT NULL,
    product_name CHARACTER VARYING(100) COLLATE pg_catalog."default" NOT NULL,
    unit_measure CHARACTER VARYING(20) COLLATE pg_catalog."default" NOT NULL,
    min_stock INTEGER NOT NULL,
    category CHARACTER VARYING(50) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT product_pkey PRIMARY KEY (product_id),
    CONSTRAINT product_name_unique UNIQUE (product_name),
    CONSTRAINT product_min_stock_check CHECK (min_stock >= 0)
);

COMMENT ON TABLE public.product IS 'Довідник товарів складу';
COMMENT ON COLUMN public.product.product_id IS 'Унікальний ідентифікатор товару';
COMMENT ON COLUMN public.product.product_name IS 'Повна назва товару';
COMMENT ON COLUMN public.product.unit_measure IS 'Одиниця виміру (шт, кг, л, м тощо)';
COMMENT ON COLUMN public.product.min_stock IS 'Мінімальний залишок для контролю запасів';
COMMENT ON COLUMN public.product.category IS 'Категорія товару для класифікації';

-- Таблиця 3: Постачання (Supply)
CREATE TABLE IF NOT EXISTS public.supply
(
    supply_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    supply_date TIMESTAMP WITH TIME ZONE NOT NULL,
    document_number CHARACTER VARYING(50) COLLATE pg_catalog."default" NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    CONSTRAINT supply_pkey PRIMARY KEY (supply_id),
    CONSTRAINT supply_document_number_unique UNIQUE (document_number),
    CONSTRAINT supply_quantity_check CHECK (quantity > 0),
    CONSTRAINT supply_unit_price_check CHECK (unit_price >= 0)
);

COMMENT ON TABLE public.supply IS 'Історія постачань товарів на склад';
COMMENT ON COLUMN public.supply.supply_id IS 'Унікальний ідентифікатор постачання';
COMMENT ON COLUMN public.supply.supplier_id IS 'Ідентифікатор постачальника';
COMMENT ON COLUMN public.supply.product_id IS 'Ідентифікатор товару';
COMMENT ON COLUMN public.supply.supply_date IS 'Дата та час надходження товару';
COMMENT ON COLUMN public.supply.document_number IS 'Номер накладної або рахунку';
COMMENT ON COLUMN public.supply.quantity IS 'Кількість товару в даному постачанні';
COMMENT ON COLUMN public.supply.unit_price IS 'Закупівельна ціна за одиницю';

-- Таблиця 4: Складський облік (Inventory)
CREATE TABLE IF NOT EXISTS public.inventory
(
    inventory_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    last_updated TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    location CHARACTER VARYING(50) COLLATE pg_catalog."default",
    CONSTRAINT inventory_pkey PRIMARY KEY (inventory_id),
    CONSTRAINT inventory_product_id_unique UNIQUE (product_id),
    CONSTRAINT inventory_quantity_check CHECK (quantity >= 0)
);

COMMENT ON TABLE public.inventory IS 'Поточний стан товарів на складі';
COMMENT ON COLUMN public.inventory.inventory_id IS 'Унікальний ідентифікатор запису обліку';
COMMENT ON COLUMN public.inventory.product_id IS 'Ідентифікатор товару (звязок 1:1)';
COMMENT ON COLUMN public.inventory.quantity IS 'Поточна кількість товару на складі';
COMMENT ON COLUMN public.inventory.last_updated IS 'Дата та час останнього оновлення залишку';
COMMENT ON COLUMN public.inventory.location IS 'Розташування товару на складі (секція, полиця)';

-- FK: Supply → Supplier
ALTER TABLE IF EXISTS public.supply
    ADD CONSTRAINT supply_supplier_id_fkey FOREIGN KEY (supplier_id)
    REFERENCES public.supplier (supplier_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE RESTRICT;

-- FK: Supply → Product
ALTER TABLE IF EXISTS public.supply
    ADD CONSTRAINT supply_product_id_fkey FOREIGN KEY (product_id)
    REFERENCES public.product (product_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE RESTRICT;

-- FK: Inventory → Product
ALTER TABLE IF EXISTS public.inventory
    ADD CONSTRAINT inventory_product_id_fkey FOREIGN KEY (product_id)
    REFERENCES public.product (product_id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE RESTRICT;

CREATE INDEX IF NOT EXISTS idx_supply_supplier_id ON public.supply(supplier_id);
CREATE INDEX IF NOT EXISTS idx_supply_product_id ON public.supply(product_id);
CREATE INDEX IF NOT EXISTS idx_supply_date ON public.supply(supply_date);
CREATE INDEX IF NOT EXISTS idx_inventory_product_id ON public.inventory(product_id);
CREATE INDEX IF NOT EXISTS idx_product_category ON public.product(category);

COMMIT;

-- Додавання постачальників
INSERT INTO public.supplier (supplier_id, company_name, contact_person, phone, email) VALUES
(1, 'ТОВ "Продукти України"', 'Іванов Іван Іванович', '+380501234567', 'ivanov@products.ua'),
(2, 'ПП "Техносервіс"', 'Петренко Петро Петрович', '+380672345678', 'petrenko@techno.ua'),
(3, 'ТзОВ "ОптТорг"', 'Сидоренко Ольга Миколаївна', '+380933456789', 'sydorenko@opttorg.ua'),
(4, 'ФОП "Євротехніка"', 'Коваленко Марія Василівна', '+380504567890', 'kovalenko@eurotech.ua'),
(5, 'ТОВ "МегаПостач"', 'Бондаренко Андрій Сергійович', '+380671234567', 'bondarenko@megasupply.ua');

-- Додавання товарів
INSERT INTO public.product (product_id, product_name, unit_measure, min_stock, category) VALUES
(1, 'Ноутбук Lenovo ThinkPad E15', 'шт', 5, 'Комп''ютерна техніка'),
(2, 'Принтер HP LaserJet Pro M404dn', 'шт', 3, 'Оргтехніка'),
(3, 'Папір офісний A4 80г/м² Снігурочка', 'уп', 50, 'Канцтовари'),
(4, 'Олівці чорнографітні HB', 'уп', 100, 'Канцтовари'),
(5, 'Монітор Dell P2422H 24"', 'шт', 10, 'Комп''ютерна техніка'),
(6, 'Клавіатура Logitech K120', 'шт', 15, 'Комп''ютерна техніка'),
(7, 'Миша Logitech M90', 'шт', 20, 'Комп''ютерна техніка'),
(8, 'Степлер металевий №24', 'шт', 30, 'Канцтовари'),
(9, 'Скобки для степлера №24/6', 'уп', 80, 'Канцтовари'),
(10, 'Тонер-картридж HP CF259A', 'шт', 5, 'Витратні матеріали');

-- Додавання постачань
INSERT INTO public.supply (supply_id, supplier_id, product_id, supply_date, document_number, quantity, unit_price) VALUES
(1, 2, 1, '2024-10-01 10:30:00+03', 'ПН-2024-001', 3.00, 15000.00),
(2, 3, 2, '2024-10-05 14:15:00+03', 'ПН-2024-002', 5.00, 2500.00),
(3, 1, 3, '2024-10-10 09:00:00+03', 'ПН-2024-003', 50.00, 75.00),
(4, 2, 5, '2024-10-01 11:00:00+03', 'ПН-2024-004', 2.00, 7500.00),
(5, 1, 4, '2024-10-10 09:30:00+03', 'ПН-2024-005', 100.00, 15.00),
(6, 4, 6, '2024-10-15 13:20:00+03', 'ПН-2024-006', 10.00, 250.00),
(7, 4, 7, '2024-10-15 13:25:00+03', 'ПН-2024-007', 15.00, 150.00),
(8, 3, 8, '2024-10-18 10:45:00+03', 'ПН-2024-008', 20.00, 120.00),
(9, 1, 9, '2024-10-20 11:15:00+03', 'ПН-2024-009', 80.00, 35.00),
(10, 5, 10, '2024-10-22 15:30:00+03', 'ПН-2024-010', 8.00, 1200.00),
(11, 2, 1, '2024-11-05 09:45:00+02', 'ПН-2024-011', 5.00, 14800.00),
(12, 3, 3, '2024-11-08 14:00:00+02', 'ПН-2024-012', 30.00, 72.00),
(13, 5, 2, '2024-11-12 10:30:00+02', 'ПН-2024-013', 3.00, 2550.00),
(14, 4, 5, '2024-11-15 11:20:00+02', 'ПН-2024-014', 7.00, 7400.00),
(15, 1, 4, '2024-11-20 08:50:00+02', 'ПН-2024-015', 50.00, 14.50);

-- Додавання складського обліку
INSERT INTO public.inventory (inventory_id, product_id, quantity, last_updated, location) VALUES
(1, 1, 8.00, '2024-11-05 09:45:00+02', 'Секція A, полиця 1'),
(2, 2, 8.00, '2024-11-12 10:30:00+02', 'Секція B, полиця 3'),
(3, 3, 80.00, '2024-11-08 14:00:00+02', 'Секція C, полиця 5'),
(4, 4, 150.00, '2024-11-20 08:50:00+02', 'Секція C, полиця 6'),
(5, 5, 9.00, '2024-11-15 11:20:00+02', 'Секція A, полиця 2'),
(6, 6, 10.00, '2024-10-15 13:20:00+03', 'Секція A, полиця 3'),
(7, 7, 15.00, '2024-10-15 13:25:00+03', 'Секція A, полиця 3'),
(8, 8, 20.00, '2024-10-18 10:45:00+03', 'Секція D, полиця 1'),
(9, 9, 80.00, '2024-10-20 11:15:00+03', 'Секція D, полиця 2'),
(10, 10, 8.00, '2024-10-22 15:30:00+03', 'Секція B, полиця 4');
