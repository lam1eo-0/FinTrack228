PRAGMA foreign_keys = ON;

-- Удаляем дочерние таблицы прежде родительских.
DROP TABLE IF EXISTS Reports;
DROP TABLE IF EXISTS Operations;
DROP TABLE IF EXISTS Categories;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Roles;

-- 1. Роли пользователей.
CREATE TABLE Roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- 2. Пользователи. Только те поля, которые есть в ER-диаграмме.
CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES Roles(role_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 3. Категории финансовых операций.
CREATE TABLE Categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('income', 'expense')),
    UNIQUE (category_name, operation_type)
);

-- 4. Доходы и расходы.
CREATE TABLE Operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    operation_date TEXT NOT NULL CHECK (operation_date GLOB '????-??-??'),
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- 5. Отчёты. Финансовые показатели вычисляются запросом, а не
-- хранятся отдельными колонками (таких полей нет на ER-диаграмме).
CREATE TABLE Reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    report_name TEXT NOT NULL,
    period_start TEXT NOT NULL CHECK (period_start GLOB '????-??-??'),
    period_end TEXT NOT NULL CHECK (period_end GLOB '????-??-??'),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (period_start <= period_end),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Тестовые записи в каждую таблицу.
INSERT INTO Roles (role_name, description) VALUES
    ('Бухгалтер', 'Основной пользователь: добавление и редактирование операций, формирование отчётов'),
    ('Руководитель', 'Просмотр операций, финансовых показателей и отчётов');

INSERT INTO Users (username, full_name, is_active, role_id) VALUES
    ('accountant', 'Иванова Анна Петровна', 1, 1),
    ('manager', 'Петров Сергей Иванович', 1, 2);

INSERT INTO Categories (category_name, operation_type) VALUES
    ('Продажа товаров', 'income'),
    ('Оказание услуг', 'income'),
    ('Аренда помещения', 'expense'),
    ('Заработная плата', 'expense'),
    ('Канцелярские товары', 'expense'),
    ('Реклама', 'expense');

INSERT INTO Operations (user_id, category_id, amount, operation_date, description) VALUES
    (1, 1, 70000, '2026-09-03', 'Продажа партии товаров'),
    (1, 2, 25000, '2026-09-08', 'Оплата консультационных услуг'),
    (1, 3, 18000, '2026-09-10', 'Аренда офиса за сентябрь'),
    (1, 4, 35000, '2026-09-15', 'Заработная плата за сентябрь'),
    (1, 5, 2500,  '2026-09-17', 'Покупка бумаги и папок'),
    (1, 1, 42000, '2026-09-23', 'Продажа товаров клиенту'),
    (1, 1, 85000, '2026-10-02', 'Продажа товаров'),
    (1, 2, 30000, '2026-10-06', 'Оказание услуг'),
    (1, 3, 18000, '2026-10-10', 'Аренда офиса за октябрь'),
    (1, 4, 35000, '2026-10-15', 'Заработная плата за октябрь'),