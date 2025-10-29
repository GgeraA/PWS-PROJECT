import pytest
from unittest.mock import Mock, MagicMock, patch
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(__file__) + '/..')

@pytest.fixture
def mock_db_connect():
    """Mock para conexión de base de datos"""
    with patch('psycopg2.connect') as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.commit = MagicMock()
        mock_conn.close = MagicMock()
        
        yield mock_connect, mock_conn, mock_cursor