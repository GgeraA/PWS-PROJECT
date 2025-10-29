"""Pruebas básicas para AuthService que SÍ funcionan"""
import pytest
from services.auth_service import AuthService
from unittest.mock import Mock, patch

def test_auth_service_exists():
    """Prueba que AuthService se puede importar"""
    assert AuthService is not None

def test_session_constants():
    """Prueba constantes de sesión"""
    assert AuthService.SESSION_DURATION_HOURS == 1
    assert AuthService.ALLOW_MULTIPLE_SESSIONS == False

@patch('services.auth_service.requests.get')
def test_get_location_from_ip_localhost(mock_get):
    """Prueba obtención de ubicación para localhost"""
    location = AuthService.get_location_from_ip("127.0.0.1")
    assert location["city"] == "Localhost"
    assert location["country"] == "Local"
    mock_get.assert_not_called()

@patch('services.auth_service.requests.get')
def test_get_location_from_ip_external(mock_get):
    """Prueba obtención de ubicación para IP externa"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'ip': '8.8.8.8',
        'city': 'Mountain View',
        'region': 'California',
        'country': 'US'
    }
    mock_get.return_value = mock_response
    
    location = AuthService.get_location_from_ip("8.8.8.8")
    assert location["city"] == "Mountain View"
    assert location["country"] == "US"

@patch('services.auth_service.requests.get')
def test_get_location_from_ip_failure(mock_get):
    """Prueba obtención de ubicación cuando falla"""
    mock_get.side_effect = Exception("Network error")
    
    location = AuthService.get_location_from_ip("192.168.1.1")
    assert location["city"] == "Unknown"
    assert location["country"] == "Unknown"