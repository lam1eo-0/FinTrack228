-- FinTrack: учёт доходов и расходов небольшой фирмы
-- Лабораторная работа № 3. Проектирование и реализация базы данных.
-- СУБД: SQLite. Скрипт создаёт структуру и тестовые записи заново.
PRAGMA foreign_keys = ON;

-- Удаление зависимых таблиц перед родительскими
DROP TABLE IF EXISTS Reports;
DROP TABLE IF EXISTS Operations;
DROP TABLE IF EXISTS Categories;
DROP TABLE IF EXISTS Users;
DROP TABLE IF EXISTS Roles;

-- Структура таблиц синхронизирована с ER-диаграммой: 
-- Roles.description, Users.username/is_active, Reports.report_name/period_start/period_end/created_at.
-- Показатели total_income, total_expense и profit сохранены для расчётов FinTrack.

-- 1. Роли пользователей: бухгалтер и руководитель
CREATE TABLE Roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE,
    description TEXT
);

-- 2. Пользователи системы
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

-- 3. Справочник категорий доходов и расходов
CREATE TABLE Categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL,
    operation_type TEXT NOT NULL CHECK (operation_type IN ('income', 'expense')),
    UNIQUE (category_name, operation_type)
);

-- 4. Финансовые операции (доходы и расходы)
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

-- 5. Сохранённые финансовые отчёты (снимки показателей на момент формирования)
CREATE TABLE Reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    report_name TEXT NOT NULL,
    period_start TEXT NOT NULL CHECK (period_start GLOB '????-??-??'),
    period_end TEXT NOT NULL CHECK (period_end GLOB '????-??-??'),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_income REAL NOT NULL CHECK (total_income >= 0),
    total_expense REAL NOT NULL CHECK (total_expense >= 0),
    profit REAL NOT NULL,
    CHECK (period_start <= period_end),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

-- Тестовые значения ролей
INSERT INTO Roles (role_name, description) VALUES
    ('Бухгалтер', 'Основной пользователь: добавление и редактирование операций, формирование отчётов'),
    ('Руководитель', 'Просмотр операций, финансовых показателей и отчётов');

-- Тестовые пользователи. Демонстрационные PBKDF2-хеши, не реальные учётные данные.
-- Пароли здесь не хранятся в открытом виде; вход в систему не реализован этой ЛР.
INSERT INTO Users (username, password_hash, full_name, is_active, role_id) VALUES
    ('accountant', 'pbkdf2_sha256$150000$demo_salt_1$16232b49608151a884d73256b1b1e22bfae1182bf6406e4cc09fa6b090a9e61d', 'Иванова Анна Петровна', 1, 1),
    ('manager', 'pbkdf2_sha256$150000$demo_salt_2$9be262cac0df7ba50d915a326a7aa2948e91009fe81157c0e9221eb4c431cf07', 'Петров Сергей Иванович', 1, 2);

-- Категории доходов и расходов
INSERT INTO Categories (category_name, operation_type) VALUES
    ('Продажа товаров', 'income'),
    ('Оказание услуг', 'income'),
    ('Аренда помещения', 'expense'),
    ('Заработная плата', 'expense'),
    ('Канцелярские товары', 'expense'),
    ('Реклама', 'expense');

-- Примеры финансовых операций за два месяца
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
    (1, 6, 7000,  '2026-10-18', 'Продвижение услуг'),
    (1, 5, 3000,  '2026-10-20', 'Канцелярские принадлежности');

-- Отчёты формируются на основе операций с помощью агрегирования SUM.
-- Таблица Reports хранит результаты на момент формирования.
INSERT INTO Reports (user_id, report_name, period_start, period_end, total_income, total_expense, profit)
SELECT 1, 'Отчёт за сентябрь 2026', '2026-09-01', '2026-09-30',
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'expense' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE -o.amount END), 0)
FROM Operations o JOIN Categories c ON c.category_id = o.category_id
WHERE o.operation_date BETWEEN '2026-09-01' AND '2026-09-30';

INSERT INTO Reports (user_id, report_name, period_start, period_end, total_income, total_expense, profit)
SELECT 1, 'Отчёт за октябрь 2026', '2026-10-01', '2026-10-31',
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'expense' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE -o.amount END), 0)
FROM Operations o JOIN Categories c ON c.category_id = o.category_id
WHERE o.operation_date BETWEEN '2026-10-01' AND '2026-10-31';

INSERT INTO Reports (user_id, report_name, period_start, period_end, total_income, total_expense, profit)
SELECT 1, 'Отчёт за сентябрь–октябрь 2026', '2026-09-01', '2026-10-31',
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'expense' THEN o.amount ELSE 0 END), 0),
       COALESCE(SUM(CASE WHEN c.operation_type = 'income' THEN o.amount ELSE -o.amount END), 0)
FROM Operations o JOIN Categories c ON c.category_id = o.category_id
WHERE o.operation_date BETWEEN '2026-09-01' AND '2026-10-31';
