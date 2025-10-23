from services.auth_service import AuthService

def test_validate_email_format():
    assert AuthService.validate_email_format("test@example.com")
    assert not AuthService.validate_email_format("bademail")

def test_validate_password_strength():
    ok, _ = AuthService.validate_password_strength("Abcd1234!")
    assert ok
    weak, _ = AuthService.validate_password_strength("123")
    assert not weak

def test_validate_user_data():
    valid, _ = AuthService.validate_user_data("Gerardo", "test@example.com", "Abc12345!")
    assert valid
    invalid, _ = AuthService.validate_user_data("", "bad", "123")
    assert not invalid

def test_validate_password_common():
    ok, _ = AuthService.validate_password_common("Abc12345!")
    assert ok
    weak, _ = AuthService.validate_password_common("password")
    assert not weak
