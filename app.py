from flask import Flask, render_template, request, redirect, url_for
from flask_swagger_ui import get_swaggerui_blueprint
import psycopg2

app = Flask(__name__, static_folder="static")

SWAGGER_URL = "/docs"                 
API_URL = "/static/swagger.yaml"      

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={"app_name": "Demo API Docs"}
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

DATABASE = {
    "dbname": "seguridad",
    "user": "postgres",      
    "password": "ggerahl08ROM#", 
    "host": "localhost",
    "port": 5432
}

class Usuario:
    def __init__(self, id=None, nombre=None, email=None, password=None, rol=None):
        self.id = id
        self.nombre = nombre
        self.email = email
        self.password = password
        self.rol = rol

    @staticmethod
    def get_all():
        conn = psycopg2.connect(**DATABASE)
        cur = conn.cursor()
        cur.execute("SELECT id, nombre, email, rol FROM usuarios ORDER BY id;")
        rows = cur.fetchall()
        conn.close()
        return [Usuario(id=r[0], nombre=r[1], email=r[2], rol=r[3]) for r in rows]

    def save(self):
        conn = psycopg2.connect(**DATABASE)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nombre, email, password, rol) VALUES (%s, %s, %s, %s)",
            (self.nombre, self.email, self.password, self.rol)
        )
        conn.commit()
        conn.close()

@app.route("/")
def home():
    return '<h2>Bienvenido Sea</h2><p>Visita la <a href="/docs"> documentación </a> o la <a href="/usuarios">lista de usuarios</a>.</p>'

@app.route("/usuarios")
def listar_usuarios():
    usuarios = Usuario.get_all()
    # Renderiza un HTML básico (crearemos templates después)
    lista = "".join([f"<li>{u.id} - {u.nombre} ({u.email}) → Rol: {u.rol}</li>" for u in usuarios])
    return f"<h1>Usuarios</h1><ul>{lista}</ul><a href='/usuarios/nuevo'>➕ Nuevo Usuario</a>"

@app.route("/usuarios/nuevo", methods=["GET", "POST"])
def nuevo_usuario():
    if request.method == "POST":
        nombre = request.form["nombre"]
        email = request.form["email"]
        password = request.form["password"]
        rol = request.form["rol"]

        user = Usuario(nombre=nombre, email=email, password=password, rol=rol)
        user.save()
        return redirect(url_for("listar_usuarios"))

    # Formulario básico sin templates
    return """
    <h1>Registrar Usuario</h1>
    <form method="POST">
      Nombre: <input type="text" name="nombre"><br><br>
      Email: <input type="email" name="email"><br><br>
      Password: <input type="password" name="password"><br><br>
      Rol: <select name="rol">
        <option value="admin">Admin</option>
        <option value="editor">Editor</option>
        <option value="lector">Lector</option>
      </select><br><br>
      <button type="submit">Guardar</button>
    </form>
    """

if __name__ == "__main__":
    app.run(port=8000, debug=True)
