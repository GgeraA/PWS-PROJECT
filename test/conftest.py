import pytest
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_db_connect():
    """Simula la conexión a la base de datos para evitar usar Postgres real"""
    with patch("psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        yield mock_connect, mock_conn, mock_cursor