from models.user import User

def get_all_users():
    users = User.get_all()
    return [u.to_dict() for u in users]

def create_user(data):
    user = User(
        name=data.get("name"),
        email=data.get("email"),
        password=data.get("password"),  # Podrías hashear aquí si quieres
        role=data.get("role"),
        two_factor_enabled=data.get("two_factor_enabled", False),
        two_factor_secret=data.get("two_factor_secret")
    )
    user.save()
    return user.to_dict()
