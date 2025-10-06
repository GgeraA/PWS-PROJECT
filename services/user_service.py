from models.user import User

def register_user(data):
    if User.find_by_email(data['email']):
        return None
    
    # Usar rol por defecto si no se proporciona o no es válido
    rol = data.get('rol', 'usuario')
    if rol not in User.ALLOWED_ROLES:
        rol = 'usuario'
        
    user = User(
        nombre=data['nombre'],
        email=data['email'],
        password=User.hash_password(data['password']),
        rol=rol,
        two_factor_enabled=data.get('two_factor_enabled', False),
        two_factor_secret=data.get('two_factor_secret')
    )
    user_id = user.save()
    return User.find_by_id(user_id)  # Retornar el usuario completo

def login_user(email, password):
    user = User.find_by_email(email)
    if user and user.check_password(password):
        return user
    return None

def get_all_users():
    users = User.get_all()
    return [user.to_dict() for user in users]  # Usar to_dict para serialización

def get_user(user_id):
    user = User.find_by_id(user_id)
    return user.to_dict() if user else None

def update_user(user_id, data):
    user = User.find_by_id(user_id)
    if not user:
        return None
        
    user.nombre = data.get('nombre', user.nombre)
    user.email = data.get('email', user.email)
    if 'password' in data:
        user.password = User.hash_password(data['password'])
    
    # Validar rol
    new_role = data.get('rol', user.rol)
    if new_role in User.ALLOWED_ROLES:
        user.rol = new_role
        
    user.two_factor_enabled = data.get('two_factor_enabled', user.two_factor_enabled)
    user.two_factor_secret = data.get('two_factor_secret', user.two_factor_secret)
    user.update()
    return user.to_dict()

def delete_user(user_id):
    return User.delete(user_id)

def assign_user_role(user_id, new_role):
    return User.set_role(user_id, new_role)

def get_users_with_roles():
    return User.get_all_with_roles()