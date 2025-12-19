import pytest
import sqlite3
import os
from unittest.mock import MagicMock, patch

from validators import validate_group_name


@pytest.fixture
def db_connection():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(20) NOT NULL UNIQUE
        )
    ''')
    conn.commit()
    yield conn
    conn.close()


def create_group_logic(conn, group_name):
    if not validate_group_name(group_name):
        return "Validation Error"

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO groups (name) VALUES (?)", (group_name,))
        conn.commit()
        return "Success"
    except sqlite3.IntegrityError:
        return "Database Error: Duplicate"


def test_integration_valid_group_creation(db_connection):
    group_name = "DevOps-2025"

    result = create_group_logic(db_connection, group_name)

    assert result == "Success"

    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM groups WHERE name = ?", (group_name,))
    data = cursor.fetchone()

    assert data is not None
    assert data[0] == "DevOps-2025"


def test_integration_invalid_group_name_blocks_db(db_connection):
    """
    Тест перевіряє захист:
    Валідатор (False) -> БД (Insert НЕ має відбутися)
    """
    bad_name = "A"  # коротке

    result = create_group_logic(db_connection, bad_name)

    assert result == "Validation Error"

    cursor = db_connection.cursor()
    cursor.execute("SELECT count(*) FROM groups")
    count = cursor.fetchone()[0]
    assert count == 0


def test_integration_duplicate_group_handling(db_connection):
    """
        Тест перевіряє обробку дублікатів:
    """
    group_name = "Python-Basics"

    result1 = create_group_logic(db_connection, group_name)

    result2 = create_group_logic(db_connection, group_name)

    # Assert
    assert result1 == "Success", "Перше створення має бути успішним"
    assert result2 == "Database Error: Duplicate", "Друге створення має повернути помилку дубліката"

    cursor = db_connection.cursor()
    cursor.execute("SELECT count(*) FROM groups WHERE name = ?", (group_name,))
    count = cursor.fetchone()[0]
    assert count == 1, "Має бути лише один запис з цією назвою"

#MOCK
def test_integration_with_mock_database_error():
    """
    Тест з Mock об'єктом, імітація помилки БД без реального з'єднання
    """

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")

    result = create_group_logic(mock_conn, "DevOps-2025")


    assert result == "Database Error: Duplicate", "Має бути оброблена помилка дубліката"

    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_not_called()


#SPY
@patch('test_integration.validate_group_name')
def test_integration_spy_validator_calls(mock_validator, db_connection):
    """
    Тест зі Spy об'єктом, відстеження викликів валідатора
    """
    mock_validator.return_value = True

    group_name = "AI-ML-2025"
    result = create_group_logic(db_connection, group_name)

    assert result == "Success"

    mock_validator.assert_called_once()

    mock_validator.assert_called_with("AI-ML-2025")

    cursor = db_connection.cursor()
    cursor.execute("SELECT name FROM groups WHERE name = ?", (group_name,))
    assert cursor.fetchone()[0] == "AI-ML-2025"
