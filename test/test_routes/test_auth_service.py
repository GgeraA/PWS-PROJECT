import pytest
from services.auth_service import AuthService
from unittest.mock import Mock, patch, MagicMock
from models.user import User
from models.user_session import UserSession

def test_validate_email_format():
    """Prueba validación de formato de email"""
    assert AuthService.validate_email_format("test@example.com") == True
    assert AuthService.validate_email_format("user.name+tag@domain.co.uk") == True
    assert AuthService.validate_email_format("bademail") == False
    assert AuthService.validate_email_format("missing@domain") == False
    assert AuthService.validate_email_format("@domain.com") == False

def test_validate_password_strength():
    """Prueba validación de fortaleza de contraseña"""
    # Contraseña fuerte
    is_strong, message = AuthService.validate_password_strength("Abcd1234!")
    assert is_strong == True
    assert "válida" in message
    
    # Contraseña corta
    is_strong, message = AuthService.validate_password_strength("Abc1!")
    assert is_strong == False
    assert "8 caracteres" in message
    
    # Sin mayúsculas
    is_strong, message = AuthService.validate_password_strength("abcd1234!")
    assert is_strong == False
    assert "mayúscula" in message
    
    # Sin números
    is_strong, message = AuthService.validate_password_strength("Abcdefgh!")
    assert is_strong == False
    assert "número" in message
    
    # Sin caracteres especiales
    is_strong, message = AuthService.validate_password_strength("Abcd1234")
    assert is_strong == False
    assert "carácter especial" in message
    
    # Con espacios
    is_strong, message = AuthService.validate_password_strength("Abcd 1234!")
    assert is_strong == False
    assert "espacios" in message

def test_validate_password_common():
    """Prueba validación de contraseñas comunes"""
    # Contraseña no común
    is_uncommon, message = AuthService.validate_password_common("Abc12345!")
    assert is_uncommon == True
    
    # Contraseñas comunes
    common_passwords = ['password', '12345678', 'qwerty', 'admin']
    for pwd in common_passwords:
        is_uncommon, message = AuthService.validate_password_common(pwd)
        assert is_uncommon == False
        assert "común" in message

def test_validate_user_data_valid():
    """Prueba validación de datos de usuario (válidos)"""
    is_valid, errors = AuthService.validate_user_data(
        "Juan Pérez", 
        "juan@example.com", 
        "SecurePass123!"
    )
    assert is_valid == True
    assert len(errors) == 0

def test_validate_user_data_invalid():
    """Prueba validación de datos de usuario (inválidos)"""
    # Nombre vacío
    is_valid, errors = AuthService.validate_user_data("", "test@example.com", "Abc123!")
    assert is_valid == False
    assert any("nombre" in error.lower() for error in errors)
    
    # Email inválido
    is_valid, errors = AuthService.validate_user_data("Juan", "bademail", "Abc123!")
    assert is_valid == False
    assert any("email" in error.lower() for error in errors)
    
    # Contraseña débil
    is_valid, errors = AuthService.validate_user_data("Juan", "test@example.com", "123")
    assert is_valid == False
    assert any("contraseña" in error.lower() for error in errors)

@patch('services.auth_service.User.find_by_email')
def test_is_email_already_registered_true(mock_find):
    """Prueba verificación de email ya registrado (True)"""
    mock_find.return_value = Mock()  # Simular usuario encontrado
    
    result = AuthService.is_email_already_registered("existing@example.com")
    assert result == True

@patch('services.auth_service.User.find_by_email')
def test_is_email_already_registered_false(mock_find):
    """Prueba verificación de email ya registrado (False)"""
    mock_find.return_value = None  # Simular usuario no encontrado
    
    result = AuthService.is_email_already_registered("new@example.com")
    assert result == False

@patch('services.auth_service.requests.get')
def test_get_location_from_ip_localhost(mock_get):
    """Prueba obtención de ubicación para localhost"""
    location = AuthService.get_location_from_ip("127.0.0.1")
    assert location["city"] == "Localhost"
    assert location["country"] == "Local"
    mock_get.assert_not_called()  # No debería hacer request para localhost

@patch('services.auth_service.requests.get')
def test_get_location_from_ip_external(mock_get):
    """Prueba obtención de ubicación para IP externa"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'ip': '8.8.8.8',
        'city': 'Mountain View',
        'region': 'California',
        'country': 'US',
        'loc': '37.4056,-122.0775',
        'timezone': 'America/Los_Angeles',
        'org': 'Google LLC'
    }
    mock_get.return_value = mock_response
    
    location = AuthService.get_location_from_ip("8.8.8.8")
    assert location["city"] == "Mountain View"
    assert location["country"] == "US"
    mock_get.assert_called_once()

def test_verify_2fa_success():
    """Prueba verificación 2FA exitosa"""
    result, status = AuthService.verify_2fa("test@example.com", "123456")
    assert status == 200
    assert result["success"] == True

def test_verify_2fa_failure():
    """Prueba verificación 2FA fallida"""
    result, status = AuthService.verify_2fa("test@example.com", "wrongcode")
    assert status == 401
    assert "inválido" in result["error"]