-- FinTrack. ЛР3. SQLite: структура соответствует ER-схеме Access.
-- Для НОВОЙ пустой базы. Существующие таблицы этот скрипт не удаляет.
-- В main.py внешние ключи включаются для каждого соединения.
PRAGMA foreign_keys = ON;
BEGIN TRANSACTION;

CREATE TABLE Roles (
    role_id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT NOT NULL UNIQUE CHECK (length(trim(role_name)) BETWEEN 1 AND 40),
    description TEXT CHECK (length(description) <= 255)
);

CREATE TABLE Users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE CHECK (length(trim(username)) BETWEEN 1 AND 50),
    full_name TEXT NOT NULL CHECK (length(trim(full_name)) BETWEEN 1 AND 100),
    role_id INTEGER NOT NULL,
    is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    FOREIGN KEY (role_id) REFERENCES Roles(role_id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE TABLE Categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT NOT NULL CHECK (length(trim(category_name)) BETWEEN 1 AND 80),
    operation_type TEXT NOT NULL CHECK (operation_type IN ('Доход', 'Расход')),
    UNIQUE (category_name, operation_type)
);

CREATE TABLE Operations (
    operation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    operation_date TEXT NOT NULL CHECK (
        length(operation_date) = 10 AND operation_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND date(operation_date, '+0 days') IS NOT NULL
        AND date(operation_date, '+0 days') = operation_date
    ),
    amount NUMERIC NOT NULL CHECK (typeof(amount) IN ('integer','real') AND amount > 0 AND amount <= 922337203685477.5807),
    category_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    description TEXT CHECK (length(description) <= 255),
    FOREIGN KEY (category_id) REFERENCES Categories(category_id) ON UPDATE RESTRICT ON DELETE RESTRICT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

-- В Reports хранятся параметры отчёта, как на диаграмме.
-- total_income, total_expense, profit вычисляются представлением qry_ReportTotals.
CREATE TABLE Reports (
    report_id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_name TEXT NOT NULL CHECK (length(trim(report_name)) BETWEEN 1 AND 100),
    period_start TEXT NOT NULL CHECK (
        length(period_start) = 10 AND period_start GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND date(period_start, '+0 days') IS NOT NULL AND date(period_start, '+0 days') = period_start
    ),
    period_end TEXT NOT NULL CHECK (
        length(period_end) = 10 AND period_end GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'
        AND date(period_end, '+0 days') IS NOT NULL AND date(period_end, '+0 days') = period_end
    ),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP CHECK (datetime(created_at) IS NOT NULL),
    user_id INTEGER NOT NULL,
    CHECK (period_end >= period_start),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON UPDATE RESTRICT ON DELETE RESTRICT
);

CREATE INDEX IX_Users_Role ON Users(role_id);
CREATE INDEX IX_Operations_Category ON Operations(category_id);
CREATE INDEX IX_Operations_User ON Operations(user_id);
CREATE INDEX IX_Operations_Date ON Operations(operation_date);
CREATE INDEX IX_Reports_User ON Reports(user_id);

CREATE VIEW qry_Operations AS
SELECT o.operation_id, o.operation_date, c.operation_type, c.category_name,
       o.amount, u.full_name, o.description
FROM Operations o JOIN Categories c ON c.category_id=o.category_id
JOIN Users u ON u.user_id=o.user_id;

CREATE VIEW qry_Income AS SELECT * FROM qry_Operations WHERE operation_type='Доход';
CREATE VIEW qry_Expenses AS SELECT * FROM qry_Operations WHERE operation_type='Расход';

CREATE VIEW qry_Balance AS
SELECT COALESCE(SUM(CASE WHEN operation_type='Доход' THEN amount ELSE 0 END),0) AS total_income,
       COALESCE(SUM(CASE WHEN operation_type='Расход' THEN amount ELSE 0 END),0) AS total_expense,
       COALESCE(SUM(CASE WHEN operation_type='Доход' THEN amount ELSE -amount END),0) AS profit
FROM qry_Operations;

CREATE VIEW qry_ReportTotals AS
SELECT r.report_id, r.report_name, r.period_start, r.period_end,
       COALESCE(SUM(CASE WHEN c.operation_type='Доход' THEN o.amount ELSE 0 END),0) AS total_income,
       COALESCE(SUM(CASE WHEN c.operation_type='Расход' THEN o.amount ELSE 0 END),0) AS total_expense,
       COALESCE(SUM(CASE WHEN c.operation_type='Доход' THEN o.amount ELSE -o.amount END),0) AS profit
FROM Reports r LEFT JOIN Operations o ON o.operation_date BETWEEN r.period_start AND r.period_end
LEFT JOIN Categories c ON c.category_id=o.category_id
GROUP BY r.report_id, r.report_name, r.period_start, r.period_end;

-- Учебные записи из проекта. Названия полей и тип операций согласованы с Access.
INSERT INTO Roles(role_name, description) VALUES
('Бухгалтер','Ведение операций и формирование отчётов'),
('Руководитель','Просмотр операций и финансовых отчётов');
INSERT INTO Users(username, full_name, role_id, is_active) VALUES
('accountant','Иванова Анна Петровна',1,1),
('manager','Петров Сергей Иванович',2,1);
INSERT INTO Categories(category_name, operation_type) VALUES
('Продажа товаров','Доход'), ('Оказание услуг','Доход'),
('Аренда помещения','Расход'), ('Заработная плата','Расход'),
('Канцелярские товары','Расход'), ('Реклама','Расход');
INSERT INTO Operations(user_id, category_id, amount, operation_date, description) VALUES
(1,1,70000,'2026-09-03','Продажа партии товаров'),
(1,2,25000,'2026-09-08','Оплата консультационных услуг'),
(1,3,18000,'2026-09-10','Аренда офиса за сентябрь'),
(1,4,35000,'2026-09-15','Заработная плата за сентябрь'),
(1,5,2500,'2026-09-17','Покупка бумаги и папок'),
(1,1,42000,'2026-09-23','Продажа товаров клиенту'),
(1,1,85000,'2026-10-02','Продажа товаров'),
(1,2,30000,'2026-10-06','Оказание услуг'),
(1,3,18000,'2026-10-10','Аренда офиса за октябрь'),
(1,4,35000,'2026-10-15','Заработная плата за октябрь'),
(1,6,7000,'2026-10-18','Продвижение услуг'),
(1,5,3000,'2026-10-20','Канцелярские принадлежности');
INSERT INTO Reports(report_name, period_start, period_end, created_at, user_id) VALUES
('Отчёт за сентябрь 2026','2026-09-01','2026-09-30','2026-10-01 09:00:00',1),
('Отчёт за октябрь 2026','2026-10-01','2026-10-31','2026-10-22 09:00:00',1),
('Отчёт за сентябрь–октябрь 2026','2026-09-01','2026-10-31','2026-10-22 09:00:00',1);
PRAGMA user_version = 3;
COMMIT;
