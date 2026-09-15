#!/usr/bin/env python3
"""Проверка согласованности openapi.yaml сверх синтаксической валидности:
уникальность operationId и корректность x-verified-status/x-verified-date/x-source.
"""
import datetime
import re
import sys

import yaml

HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
VERIFIED_STATUSES = {"live", "extrapolated", "third-party", "untested"}
SOURCED_STATUSES = {"extrapolated", "third-party"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def check_verified_block(block, where, errors, today):
    status = block.get("x-verified-status")
    if status is None:
        return

    if status not in VERIFIED_STATUSES:
        errors.append(f"{where}: x-verified-status={status!r} — не входит в {sorted(VERIFIED_STATUSES)}")
        return

    date = block.get("x-verified-date")
    if status == "live":
        if not date:
            errors.append(f"{where}: x-verified-status=live без x-verified-date")
        elif not DATE_RE.match(str(date)):
            errors.append(f"{where}: x-verified-date={date!r} не в формате YYYY-MM-DD")
        else:
            if datetime.date.fromisoformat(str(date)) > today:
                errors.append(f"{where}: x-verified-date={date} — дата в будущем")
    elif date:
        errors.append(f"{where}: x-verified-date указана при status={status!r} (дата допустима только для live)")

    if status in SOURCED_STATUSES:
        source = block.get("x-source")
        if not source or not str(source).strip():
            errors.append(f"{where}: x-verified-status={status!r} без непустого x-source")


def check_sources(node, where, errors):
    if isinstance(node, dict):
        if "x-source" in node and "x-verified-status" not in node:
            value = node["x-source"]
            if not value or not str(value).strip():
                errors.append(f"{where}: пустой x-source")
        for key, value in node.items():
            check_sources(value, f"{where}.{key}", errors)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            check_sources(value, f"{where}[{i}]", errors)


def main(path):
    with open(path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    errors = []
    today = datetime.date.today()
    operation_ids = {}

    for path_key, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method not in HTTP_METHODS or not isinstance(op, dict):
                continue
            where = f"{method.upper()} {path_key}"

            op_id = op.get("operationId")
            if not op_id:
                errors.append(f"{where}: нет operationId")
            elif op_id in operation_ids:
                errors.append(f"{where}: дублирует operationId {op_id!r} (уже использован в {operation_ids[op_id]})")
            else:
                operation_ids[op_id] = where

            if "x-verified-status" not in op:
                errors.append(f"{where}: нет x-verified-status")
            check_verified_block(op, where, errors, today)

            for status_code, resp in (op.get("responses") or {}).items():
                if isinstance(resp, dict):
                    check_verified_block(resp, f"{where} [{status_code}]", errors, today)

    check_sources(spec, "root", errors)

    if errors:
        print(f"Найдено {len(errors)} несоответствий в {path}:\n")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(operation_ids)} operationId, x-verified-status/x-source согласованы")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "openapi.yaml"))
