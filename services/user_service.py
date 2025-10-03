from models.user import User


# Registrar usuario
def register_user(data):
    if User.find_by_email(data['email']):
        return None  # Ya existe
    user = User(
        nombre=data['nombre'],
        email=data['email'],
        password=User.hash_password(data['password']),
        rol=data.get('rol', 'user'),
        two_factor_enabled=data.get('two_factor_enabled', False),
        two_factor_secret=data.get('two_factor_secret')
    )
    user.save()
    return user

# Iniciar sesión
def login_user(email, password):
    user = User.find_by_email(email)
    if user and user.check_password(password):
        return user
    return None

# Obtener todos los usuarios
def get_all_users():
    return User.get_all()

# Obtener usuario por ID
def get_user(user_id):
    return User.find_by_id(user_id)

# Actualizar usuario
def update_user(user_id, data):
    user = User.find_by_id(user_id)
    if not user:
        return None
    user.nombre = data.get('nombre', user.nombre)
    user.email = data.get('email', user.email)
    if 'password' in data:
        user.password = User.hash_password(data['password'])
    user.rol = data.get('rol', user.rol)
    user.two_factor_enabled = data.get('two_factor_enabled', user.two_factor_enabled)
    user.two_factor_secret = data.get('two_factor_secret', user.two_factor_secret)
    user.update()
    return user

# Eliminar usuario
def delete_user(user_id):
    return User.delete(user_id)
