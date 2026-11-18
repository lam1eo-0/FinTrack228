"""Экспорт таблицы SQLite и связанных записей в JSON, CSV, XML и YAML."""

import argparse
import csv
import json
from pathlib import Path
import sqlite3
from xml.etree.ElementTree import register_namespace
import xml.etree.ElementTree as ET

import database


register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")


def quote_identifier(value):
    return '"' + value.replace('"', '""') + '"'


def table_names(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    return {row[0] for row in rows}


def related_record(conn, table, row, known_tables, visited):
    result = dict(row)
    if "password_hash" in result:
        result.pop("password_hash")

    for foreign_key in conn.execute(f"PRAGMA foreign_key_list({quote_identifier(table)})"):
        referenced_table = foreign_key["table"]
        source_column = foreign_key["from"]
        target_column = foreign_key["to"]
        relation_name = referenced_table.lower()
        if referenced_table not in known_tables or relation_name in visited:
            continue

        key = result.get(source_column)
        nested = None
        if key is not None:
            sql = (
                f"SELECT * FROM {quote_identifier(referenced_table)} "
                f"WHERE {quote_identifier(target_column)} = ?"
            )
            related_row = conn.execute(sql, (key,)).fetchone()
            if related_row is not None:
                nested = related_record(
                    conn, referenced_table, related_row, known_tables, visited | {relation_name}
                )
        result[relation_name] = nested
    return result


def extract_records(conn, table):
    known_tables = table_names(conn)
    if table not in known_tables:
        raise ValueError(f"Таблица {table!r} не найдена. Доступны: {', '.join(sorted(known_tables))}")
    rows = conn.execute(f"SELECT * FROM {quote_identifier(table)}").fetchall()
    visited = {table.lower()}
    return [related_record(conn, table, row, known_tables, visited) for row in rows]


def yaml_scalar(value):
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return json.dumps(value, ensure_ascii=False, allow_nan=False)
    return json.dumps(str(value), ensure_ascii=False)


def yaml_lines(value, indent=0):
    prefix = " " * indent
    if isinstance(value, dict):
        lines = []
        for key, item in value.items():
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}{yaml_scalar(key)}:")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}{yaml_scalar(key)}: {yaml_scalar(item)}")
        return lines
    if isinstance(value, list):
        lines = []
        for item in value:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                lines.extend(yaml_lines(item, indent + 2))
            else:
                lines.append(f"{prefix}- {yaml_scalar(item)}")
        return lines
    return [f"{prefix}{yaml_scalar(value)}"]


def xml_element(parent, name, value):
    element = ET.SubElement(parent, name)
    if isinstance(value, dict):
        for key, item in value.items():
            xml_element(element, key, item)
    elif isinstance(value, list):
        for item in value:
            xml_element(element, "item", item)
    elif value is None:
        element.set("{http://www.w3.org/2001/XMLSchema-instance}nil", "true")
    else:
        element.text = str(value)
    return element


def csv_value(value):
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def export_table(database_path, table, output_dir):
    with sqlite3.connect(Path(database_path).resolve().as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        records = extract_records(conn, table)
        columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({quote_identifier(table)})")]
        relation_columns = [
            foreign_key["table"].lower()
            for foreign_key in conn.execute(f"PRAGMA foreign_key_list({quote_identifier(table)})")
        ]

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "data.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    with (output_dir / "data.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns + relation_columns, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow({key: csv_value(value) for key, value in record.items()})

    root = ET.Element(table.lower())
    for record in records:
        xml_element(root, "record", record)
    ET.indent(root, space="  ")
    (output_dir / "data.xml").write_bytes(
        ET.tostring(root, encoding="utf-8", xml_declaration=True)
    )

    (output_dir / "data.yaml").write_text("\n".join(yaml_lines(records)) + "\n", encoding="utf-8")
    return len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", default="Operations", help="таблица SQLite для экспорта")
    parser.add_argument("--database", help="путь к файлу SQLite")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "out")
    args = parser.parse_args()
    database_path = Path(args.database).resolve() if args.database else database.DATABASE_PATH
    try:
        count = export_table(database_path, args.table, args.out)
    except (OSError, sqlite3.DatabaseError, ValueError) as error:
        parser.error(str(error))
    print(f"Экспортировано записей: {count}")
    print(f"Файлы сохранены в: {args.out.resolve()}")


if __name__ == "__main__":
    main()
