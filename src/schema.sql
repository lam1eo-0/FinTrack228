-- FinTrack. SQLite. Повторный запуск заменяет таблицы тестовыми данными.
PRAGMA foreign_keys = ON;
BEGIN IMMEDIATE;

DROP TABLE IF EXISTS Reports;
DROP TABLE IF EXISTS Operations;
DROP TABLE IF EXISTS Categories;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Roles;

CREATE TABLE Roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    role_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES Roles(role_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE Categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('income', 'expense')),
    UNIQUE (category_name, operation_type)
);

CREATE TABLE Operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK (amount > 0),
    operation_date TEXT NOT NULL CHECK (operation_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(operation_date, '+0 days') IS NOT NULL AND date(operation_date, '+0 days') = operation_date),
    description TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (category_id) REFERENCES Categories(category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Отчёт хранит период, автора и снимок итогов на момент формирования.
CREATE TABLE Reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    report_name TEXT NOT NULL,
    period_start TEXT NOT NULL CHECK (period_start GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(period_start, '+0 days') IS NOT NULL AND date(period_start, '+0 days') = period_start),
    period_end TEXT NOT NULL CHECK (period_end GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(period_end, '+0 days') IS NOT NULL AND date(period_end, '+0 days') = period_end),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_income REAL NOT NULL CHECK (total_income >= 0),
    total_expense REAL NOT NULL CHECK (total_expense >= 0),
    profit REAL NOT NULL,
    CHECK (period_start <= period_end),
    CHECK (ABS(profit - (total_income - total_expense)) < 0.005),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

INSERT INTO Roles (role_id, role_name, description) VALUES
    (1, 'Бухгалтер', 'Ведение операций и формирование отчётов'),
    (2, 'Руководитель', 'Просмотр и поиск операций и отчётов');

INSERT INTO Users (user_id, username, password_hash, full_name, is_active, role_id) VALUES
    (1, 'accountant', 'pbkdf2_sha256$260000$3a09937b2a0c3cbf7238228026300737$315bb122d7d25980d7e90468271fb7d77e3deb966f762d5b2893d5cdab9a73b2', 'Иванова Анна Петровна', 1, 1),
    (2, 'manager', 'pbkdf2_sha256$260000$f38cc396a64d67dc7737c40c1ce12463$50756d0f747a8f7bd8046256187ac18fb9e0656557736bf2732c31dccdcbe6d7', 'Петров Сергей Иванович', 1, 2);

INSERT INTO Categories (category_id, category_name, operation_type) VALUES
    (1, 'Продажа товаров', 'income'),
    (2, 'Оказание услуг', 'income'),
    (3, 'Аренда помещения', 'expense'),
    (4, 'Заработная плата', 'expense'),
    (5, 'Канцелярские товары', 'expense'),
    (6, 'Реклама', 'expense');

INSERT INTO Operations (operation_id, user_id, category_id, amount, operation_date, description) VALUES
    (1, 1, 1, 70000.0, '2026-09-03', 'Продажа партии товаров'),
    (2, 1, 2, 25000.0, '2026-09-08', 'Оплата консультационных услуг'),
    (3, 1, 3, 18000.0, '2026-09-10', 'Аренда офиса за сентябрь'),
    (4, 1, 4, 35000.0, '2026-09-15', 'Заработная плата за сентябрь'),
    (5, 1, 5, 2500.0, '2026-09-17', 'Покупка бумаги и папок'),
    (6, 1, 1, 42000.0, '2026-09-23', 'Продажа товаров клиенту'),
    (7, 1, 1, 85000.0, '2026-10-02', 'Продажа товаров'),
    (8, 1, 2, 30000.0, '2026-10-06', 'Оказание услуг'),
    (9, 1, 3, 18000.0, '2026-10-10', 'Аренда офиса за октябрь'),
    (10, 1, 4, 35000.0, '2026-10-15', 'Заработная плата за октябрь'),
    (11, 1, 6, 7000.0, '2026-10-18', 'Продвижение услуг'),
    (12, 1, 5, 3000.0, '2026-10-20', 'Канцелярские принадлежности');

-- Итоги формируются из операций за период всей фирмы. user_id обозначает автора.

INSERT INTO Reports (report_id, user_id, report_name, period_start, period_end,
                     total_income, total_expense, profit)
SELECT 1, 1, 'Отчёт за сентябрь 2026', '2026-09-01', '2026-09-30',
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'expense' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE -o.amount END), 0)
FROM Operations AS o
JOIN Categories AS c ON c.category_id = o.category_id
WHERE o.operation_date BETWEEN '2026-09-01' AND '2026-09-30';

INSERT INTO Reports (report_id, user_id, report_name, period_start, period_end,
                     total_income, total_expense, profit)
SELECT 2, 1, 'Отчёт за октябрь 2026', '2026-10-01', '2026-10-31',
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'expense' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE -o.amount END), 0)
FROM Operations AS o
JOIN Categories AS c ON c.category_id = o.category_id
WHERE o.operation_date BETWEEN '2026-10-01' AND '2026-10-31';

INSERT INTO Reports (report_id, user_id, report_name, period_start, period_end,
                     total_income, total_expense, profit)
SELECT 3, 1, 'Отчёт за сентябрь и октябрь 2026', '2026-09-01', '2026-10-31',
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'expense' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE -o.amount END), 0)
FROM Operations AS o
JOIN Categories AS c ON c.category_id = o.category_id
WHERE o.operation_date BETWEEN '2026-09-01' AND '2026-10-31';

COMMIT;
