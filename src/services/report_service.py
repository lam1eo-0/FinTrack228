from models import FinancialSummary
from repositories.operation_repository import OperationRepository
from repositories.report_repository import ReportRepository
from services.common import ServiceError, require_user, required_text, session, valid_period


def calculate(conn, start, end):
    income, expense = OperationRepository(conn).get_totals(start, end)
    return FinancialSummary(start, end, income, expense, round(income - expense, 2))


def get_summary(actor_id, start, end):
    start, end = valid_period(start, end)
    with session() as conn:
        require_user(conn, actor_id)
        return calculate(conn, start, end)


def list_reports(actor_id):
    with session() as conn:
        require_user(conn, actor_id)
        return ReportRepository(conn).get_all()


def get_report(actor_id, report_id):
    with session() as conn:
        require_user(conn, actor_id)
        report = ReportRepository(conn).get_by_id(report_id)
        if report is None:
            raise ServiceError("Отчёт не найден.")
        return report


def save_report(actor_id, name, start, end, report_id=None):
    name = required_text(name, "Название отчёта")
    start, end = valid_period(start, end)
    with session(write=True) as conn:
        require_user(conn, actor_id, accountant=True)
        reports = ReportRepository(conn)
        if report_id is not None and reports.get_by_id(report_id) is None:
            raise ServiceError("Отчёт не найден.")
        summary = calculate(conn, start, end)
        if report_id is None:
            return reports.create(actor_id, name, summary)
        return reports.update(report_id, actor_id, name, summary)


def delete_report(actor_id, report_id):
    with session(write=True) as conn:
        require_user(conn, actor_id, accountant=True)
        reports = ReportRepository(conn)
        if reports.get_by_id(report_id) is None:
            raise ServiceError("Отчёт не найден.")
        return reports.delete(report_id)
