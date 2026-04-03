import platform
import subprocess
import time
from pathlib import Path

import mysql.connector
from mysql.connector import pooling

from config.settings import (
    MYSQL_AUTO_START_SERVICE,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
    MYSQL_WINDOWS_SERVICE_NAME,
)


BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "schema.sql"

_pool = None


def _is_local_mysql():
    return MYSQL_HOST in {"localhost", "127.0.0.1"}


def _try_start_windows_mysql_service():
    if not MYSQL_AUTO_START_SERVICE:
        return

    if platform.system() != "Windows":
        return

    if not _is_local_mysql():
        return

    service_name = MYSQL_WINDOWS_SERVICE_NAME.strip()
    if not service_name:
        return

    try:
        query_result = subprocess.run(
            ["sc.exe", "query", service_name],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
        output = (query_result.stdout or "") + (query_result.stderr or "")
        if "RUNNING" in output:
            return

        subprocess.run(
            ["sc.exe", "start", service_name],
            capture_output=True,
            text=True,
            check=False,
            timeout=15,
        )
        time.sleep(2)
    except Exception:
        # Best-effort startup only; connection code will still raise the real DB error if needed.
        return


def _bootstrap_connection():
    _try_start_windows_mysql_service()
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
    )


def ensure_database():
    connection = _bootstrap_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def get_pool():
    global _pool

    if _pool is None:
        ensure_database()
        _pool = pooling.MySQLConnectionPool(
            pool_name="secure_daddy_pool",
            pool_size=5,
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            autocommit=False,
        )

    return _pool


def get_db_connection():
    return get_pool().get_connection()


def init_db():
    statements = [
        statement.strip()
        for statement in SCHEMA_PATH.read_text(encoding="utf-8").split(";")
        if statement.strip()
    ]

    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
        connection.commit()
    finally:
        cursor.close()
        connection.close()
