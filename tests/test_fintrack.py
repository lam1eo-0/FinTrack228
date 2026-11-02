"""Проверки бизнес-сценариев на отдельной базе для каждого теста."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import is_dataclass
from pathlib import Path
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import database
from models import Category, Operation, Report, Role, User
from repositories.category_repository import CategoryRepository
from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository
from services import auth_service, category_service, operation_service, report_service, user_service
from services.common import ServiceError
from services.diagnostics_service import check_database


class FinTrackTests(unittest.TestCase):
    def setUp(self):
        self.original_path = database.DATABASE_PATH
        self.temp = tempfile.TemporaryDirectory(prefix="fintrack-test-", dir=ROOT / "tests")
        self.folder = Path(self.temp.name).resolve()
        self.assertTrue(self.folder.is_relative_to(ROOT / "tests"))
        self.path = self.folder / "test.db"
        database.configure(self.path)
        database.initialize()

    def tearDown(self):
        database.configure(self.original_path)
        self.temp.cleanup()

    def cli(self, text="", *args, cwd=ROOT):
        return subprocess.run(
            [sys.executable, str(ROOT / "src/main.py"), "--database", str(self.path), *args],
            input=text, text=True, encoding="utf-8", capture_output=True, cwd=cwd,
            env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=30,
        )

    def test_models_and_seed(self):
        for model in (Role, User, Category, Operation, Report):
            self.assertTrue(is_dataclass(model))
        tables, integrity, keys = check_database()
        self.assertEqual([count for _, count, _ in tables], [2, 2, 6, 12, 3])
        self.assertEqual(integrity, [("ok",)])
        self.assertEqual(keys, [])

    def test_login_and_bad_password(self):
        self.assertEqual(auth_service.authenticate("ACCOUNTANT", "Accountant2026!").role_name, "Бухгалтер")
        self.assertEqual(auth_service.authenticate("manager", "Manager2026!").role_name, "Руководитель")
        with self.assertRaises(ServiceError):
            auth_service.authenticate("accountant", "incorrect")
        with self.assertRaises(ServiceError):
            auth_service.authenticate("missing", "incorrect")

    def test_registration_and_duplicate_login(self):
        user = auth_service.register("New_User", "Strong2026!", "Новый пользователь")
        self.assertEqual(user.username, "new_user")
        self.assertEqual(user.role_name, "Руководитель")
        self.assertNotIn("Strong2026!", user.password_hash)
        self.assertEqual(auth_service.authenticate("NEW_USER", "Strong2026!").user_id, user.user_id)
        with self.assertRaises(ServiceError):
            auth_service.register("NEW_USER", "Strong2026!", "Другой пользователь")

    def test_registration_validation(self):
        for username, password, full_name in [("x", "Strong2026!", "Имя"), ("normal", "short", "Имя"),
                                              ("normal", "Strong2026!", "  ")]:
            with self.subTest(username=username, password_length=len(password)):
                with self.assertRaises(ServiceError):
                    auth_service.register(username, password, full_name)

    def test_password_change(self):
        with self.assertRaises(ServiceError):
            auth_service.change_password(2, "wrong", "NewPassword2026!")
        auth_service.change_password(2, "Manager2026!", "NewPassword2026!")
        with self.assertRaises(ServiceError):
            auth_service.authenticate("manager", "Manager2026!")
        self.assertEqual(auth_service.authenticate("manager", "NewPassword2026!").user_id, 2)

    def test_inactive_user_and_live_permission_check(self):
        actor = auth_service.authenticate("manager", "Manager2026!")
        user_service.update_user(1, 2, actor.full_name, 2, 0)
        with self.assertRaises(ServiceError):
            auth_service.authenticate("manager", "Manager2026!")
        with self.assertRaises(ServiceError):
            operation_service.list_operations(actor.user_id)

    def test_manager_cannot_write(self):
        actions = [
            lambda: operation_service.save_operation(2, 1, "10", "2026-11-01"),
            lambda: operation_service.delete_operation(2, 1),
            lambda: category_service.save_category(2, "Категория", "income"),
            lambda: category_service.delete_category(2, 1),
            lambda: report_service.save_report(2, "Отчёт", "2026-09-01", "2026-09-30"),
            lambda: report_service.delete_report(2, 1),
            lambda: user_service.create_user(2, "extra", "Strong2026!", "Имя", 1),
            lambda: user_service.update_user(2, 1, "Имя", 2, 1),
            lambda: user_service.delete_user(2, 1),
        ]
        for action in actions:
            with self.assertRaises(ServiceError):
                action()

    def test_current_role_is_rechecked(self):
        second = user_service.create_user(1, "second", "Strong2026!", "Бухгалтер 2", 1)
        user_service.update_user(1, second.user_id, second.full_name, 2, 1)
        with self.assertRaises(ServiceError):
            operation_service.save_operation(second.user_id, 1, 5, "2026-11-01")

    def test_user_crud(self):
        user = user_service.create_user(1, "assistant", "Strong2026!", "Помощник", 1)
        updated = user_service.update_user(1, user.user_id, "Новое имя", 2, 1)
        self.assertEqual((updated.full_name, updated.role_name), ("Новое имя", "Руководитель"))
        self.assertTrue(user_service.delete_user(1, user.user_id))
        self.assertEqual(len(user_service.list_users(1)), 2)

    def test_last_accountant_protected(self):
        for action in [lambda: user_service.update_user(1, 1, "Имя", 2, 1),
                       lambda: user_service.update_user(1, 1, "Имя", 1, 0),
                       lambda: user_service.delete_user(1, 1)]:
            with self.assertRaises(ServiceError):
                action()

    def test_user_with_history_cannot_be_deleted(self):
        second = user_service.create_user(1, "second", "Strong2026!", "Бухгалтер 2", 1)
        with self.assertRaises(ServiceError):
            user_service.delete_user(second.user_id, 1)
        self.assertEqual(len(operation_service.list_operations(1)), 12)

    def test_category_crud_and_unicode_duplicate(self):
        category = category_service.save_category(1, "  Новая категория  ", "income")
        with self.assertRaises(ServiceError):
            category_service.save_category(1, "НОВАЯ КАТЕГОРИЯ", "income")
        updated = category_service.save_category(1, "Другой вид", "expense", category.category_id)
        self.assertEqual(updated.operation_type, "expense")
        self.assertTrue(category_service.delete_category(1, category.category_id))

    def test_used_category_protected(self):
        with self.assertRaises(ServiceError):
            category_service.delete_category(1, 1)
        with self.assertRaises(ServiceError):
            category_service.save_category(1, "Продажи", "expense", 1)

    def test_operation_crud_and_original_author(self):
        op = operation_service.save_operation(1, 1, "123,45", "2026-11-01", "Тест", expected_type="income")
        self.assertEqual(op.amount, 123.45)
        self.assertEqual(op.category_name, "Продажа товаров")
        second = user_service.create_user(1, "second", "Strong2026!", "Бухгалтер 2", 1)
        updated = operation_service.save_operation(second.user_id, 3, "50", "2026-11-02", "Правка", op.operation_id)
        self.assertEqual(updated.user_id, 1)
        self.assertEqual(updated.operation_type, "expense")
        self.assertTrue(operation_service.delete_operation(1, op.operation_id))
        with self.assertRaises(ServiceError):
            operation_service.get_operation(1, op.operation_id)

    def test_operation_validation_and_no_partial_write(self):
        for amount in ["0", "-1", "abc", "NaN", "Infinity", "1.001", "1e9999"]:
            with self.subTest(amount=amount):
                with self.assertRaises(ServiceError):
                    operation_service.save_operation(1, 1, amount, "2026-11-01")
        for day in ["2026-02-30", "2026-13-01", "20261101", "2026-1-1"]:
            with self.assertRaises(ServiceError):
                operation_service.save_operation(1, 1, "10", day)
        with self.assertRaises(ServiceError):
            operation_service.save_operation(1, 9999, "10", "2026-11-01")
        with self.assertRaises(ServiceError):
            operation_service.save_operation(1, 3, "10", "2026-11-01", expected_type="income")
        self.assertEqual(len(operation_service.list_operations(1)), 12)

    def test_operation_search(self):
        found = operation_service.list_operations(2, "2026-09-01", "2026-09-30", "АРЕНДА", "expense")
        self.assertEqual([op.operation_id for op in found], [3])
        self.assertEqual(operation_service.list_operations(2, query="' OR 1=1 --"), [])

    def test_report_totals_and_empty_period(self):
        summary = report_service.get_summary(2, "2026-09-01", "2026-09-30")
        self.assertEqual((summary.total_income, summary.total_expense, summary.profit), (137000, 55500, 81500))
        empty = report_service.save_report(1, "Пустой", "2025-01-01", "2025-01-31")
        self.assertEqual((empty.total_income, empty.total_expense, empty.profit), (0, 0, 0))
        with self.assertRaises(ServiceError):
            report_service.save_report(1, "Неверный", "2026-10-01", "2026-09-01")

    def test_report_snapshot_update_and_delete(self):
        report = report_service.save_report(1, "Ноябрь", "2026-11-01", "2026-11-30")
        operation_service.save_operation(1, 1, "10.25", "2026-11-01")
        self.assertEqual(report_service.get_report(2, report.report_id).profit, 0)
        second = user_service.create_user(1, "second", "Strong2026!", "Бухгалтер 2", 1)
        updated = report_service.save_report(second.user_id, "Обновлённый", "2026-11-01", "2026-11-30", report.report_id)
        self.assertEqual((updated.profit, updated.user_id), (10.25, second.user_id))
        self.assertTrue(report_service.delete_report(1, report.report_id))
        with self.assertRaises(ServiceError):
            report_service.get_report(1, report.report_id)

    def test_role_repository_crud_and_fk(self):
        with database.get_connection(write=True) as conn:
            roles = RoleRepository(conn)
            role = roles.create("Тестовая", "Описание")
            self.assertEqual(roles.update(role.role_id, "Временная").role_name, "Временная")
            self.assertTrue(roles.delete(role.role_id))
        with self.assertRaises(sqlite3.IntegrityError):
            with database.get_connection(write=True) as conn:
                RoleRepository(conn).delete(1)

    def test_failed_transaction_rolls_back(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with database.get_connection(write=True) as conn:
                CategoryRepository(conn).create("Откат", "income")
                UserRepository(conn).create("invalid", "hash", "Имя", 999)
        self.assertFalse(any(c.category_name == "Откат" for c in category_service.list_categories(1)))

    def test_concurrent_registration_same_login(self):
        def register():
            try:
                auth_service.register("parallel", "Strong2026!", "Параллельный")
                return True
            except ServiceError:
                return False
        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(lambda _: register(), range(2)))
        self.assertEqual(sorted(results), [False, True])

    def test_cli_manager_and_invalid_input(self):
        result = self.cli("wrong\n1\nmanager\nManager2026!\n1\n3\n2026-09-01\n2026-09-30\n0\n0\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("введите номер пункта", result.stdout)
        self.assertIn("81500.00", result.stdout)
        self.assertNotIn("7. Добавить доход", result.stdout)
        self.assertNotIn("pbkdf2", result.stdout)

    def test_cli_registration_and_login(self):
        result = self.cli("2\nreader\nНовый руководитель\nStrong2026!\nStrong2026!\n1\nreader\nStrong2026!\n0\n0\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("зарегистрирован", result.stdout)
        self.assertIn("Выполнен вход", result.stdout)

    def test_cli_operation_report_and_persistence(self):
        result = self.cli(
            "1\naccountant\nAccountant2026!\n"
            "7\n1\n100,50\n2026-11-01\nПроверка CLI\n"
            "12\n2\nНоябрь CLI\n2026-11-01\n2026-11-30\n0\n0\n0\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Операция 13 сохранена", result.stdout)
        self.assertIn("Отчёт 4 сохранён", result.stdout)
        restart = self.cli("1\nmanager\nManager2026!\n4\n0\n0\n", cwd=ROOT / "src")
        self.assertIn("Ноябрь CLI", restart.stdout)
        self.assertIn("100.50", restart.stdout)
        self.assertEqual(len(operation_service.list_operations(1)), 13)

    def test_cli_init_refuses_overwrite_and_check_any_cwd(self):
        before = self.path.read_bytes()
        result = self.cli("", "--init")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(before, self.path.read_bytes())
        result = self.cli("", "--check", cwd=self.folder)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Roles: 2", result.stdout)

    def test_cli_category_create_edit_delete(self):
        result = self.cli(
            "1\naccountant\nAccountant2026!\n11\n"
            "2\nНовая CLI\n2\n3\n7\nИсправленная CLI\n1\n4\n7\nда\n0\n0\n0\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Ошибка:", result.stdout)
        self.assertIn("Категория удалена", result.stdout)
        self.assertEqual(len(category_service.list_categories(1)), 6)

    def test_cli_operation_edit_delete(self):
        result = self.cli(
            "1\naccountant\nAccountant2026!\n9\n1\n\n70001\n\nИзменено CLI\n10\n1\nда\n0\n0\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Ошибка:", result.stdout)
        self.assertIn("Операция 1 сохранена", result.stdout)
        self.assertIn("Операция удалена", result.stdout)
        self.assertEqual(len(operation_service.list_operations(1)), 11)

    def test_cli_report_edit_delete(self):
        result = self.cli(
            "1\naccountant\nAccountant2026!\n12\n3\n1\nПравка CLI\n\n\n4\n1\nда\n0\n0\n0\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Ошибка:", result.stdout)
        self.assertIn("Отчёт 1 сохранён", result.stdout)
        self.assertIn("Отчёт удалён", result.stdout)
        self.assertEqual(len(report_service.list_reports(1)), 2)

    def test_cli_user_create_edit_delete(self):
        result = self.cli(
            "1\naccountant\nAccountant2026!\n13\n"
            "2\ncli_user\nНовый бухгалтер\nStrong2026!\nStrong2026!\n1\n"
            "3\n3\nНовое имя\n2\n0\n4\n3\nда\n5\n0\n0\n0\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Ошибка:", result.stdout)
        self.assertIn("Пользователь cli_user создан", result.stdout)
        self.assertIn("Пользователь удалён", result.stdout)
        self.assertEqual(len(user_service.list_users(1)), 2)


if __name__ == "__main__":
    unittest.main()
