from flask_restx import Namespace, Resource, fields
from models.user import User
from werkzeug.security import generate_password_hash

# Crear Namespace para usuarios
api = Namespace("users", description="Operaciones de usuarios")

# Modelo para documentación Swagger
user_model = api.model('User', {
    'nombre': fields.String(required=True, description='Nombre del usuario'),
    'email': fields.String(required=True, description='Email del usuario'),
    'password': fields.String(required=True, description='Contraseña del usuario'),
    'rol': fields.String(required=True, description='Rol del usuario')
})

# Endpoint para listar todos los usuarios
@api.route("/login")
class UsersList(Resource):
    def get(self):
        usuarios = User.get_all()
        return [{"nombre": u.nombre, "email": u.email, "rol": u.rol} for u in usuarios]

    @api.expect(user_model)
    def post(self):
        data = api.payload
        hashed = generate_password_hash(data['password'])
        user = User(
            nombre=data['nombre'],
            email=data['email'],
            password=hashed,
            rol=data['rol']
        )
        user.save()
        return {"message": "Usuario creado"}, 201
