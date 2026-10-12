import os
import secrets
import sqlite3

import bcrypt
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, session

load_dotenv()

DB_PATH = "tareas.db"
MAX_BYTES_PASSWORD = 72


def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT NOT NULL UNIQUE,
                contraseña TEXT NOT NULL
            )
        ''')
        conn.commit()
    finally:
        conn.close()


def agregar_usuario(usuario, contrasenia):
    hashed_pass = bcrypt.hashpw(contrasenia.encode("utf-8"), bcrypt.gensalt())

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO usuarios (usuario, contraseña) VALUES (?, ?)",
            (usuario, hashed_pass),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def verificar_usuario(usuario, contrasenia):
    conn = sqlite3.connect(DB_PATH)
    try:
        result = conn.execute(
            "SELECT contraseña FROM usuarios WHERE usuario = ?", (usuario,)
        ).fetchone()
    finally:
        conn.close()

    if not result:
        return False

    hashed_pass = result[0]
    if isinstance(hashed_pass, str):
        hashed_pass = hashed_pass.encode("utf-8")
    return bcrypt.checkpw(contrasenia.encode("utf-8"), hashed_pass)


def request_valido(req, campos):
    """Devuelve (True, data) o (False, (respuesta_json, status))."""
    data = req.get_json(silent=True)

    if not isinstance(data, dict):
        return False, (jsonify({"error": "Solicitud inválida"}), 400)

    for campo, tipo in campos.items():
        valor = data.get(campo)
        if not isinstance(valor, tipo) or not valor:
            return False, (jsonify({"error": "Solicitud inválida"}), 400)

    if len(data["contraseña"].encode("utf-8")) > MAX_BYTES_PASSWORD:
        return False, (jsonify({"error": "Solicitud inválida"}), 400)

    return True, data


app = Flask(__name__)


app.secret_key = os.getenv("SECRET_KEY") or secrets.token_hex(32)
debug_mode = os.getenv("DEBUG_MODE", "False").lower() == "true"

init_db()


@app.route("/")
def home():
    return jsonify({"mensaje": "Bienvenido a la API de tareas"}), 200


@app.route("/registro", methods=["POST"])
def crear_usuario():
    valido, resultado = request_valido(request, {"usuario": str, "contraseña": str})
    if not valido:
        return resultado

    if agregar_usuario(resultado["usuario"], resultado["contraseña"]):
        return jsonify({"mensaje": "Usuario creado exitosamente"}), 201
    return jsonify({"error": "El usuario ya existe"}), 409


@app.route("/login", methods=["POST"])
def login():
    valido, resultado = request_valido(request, {"usuario": str, "contraseña": str})
    if not valido:
        return resultado

    if verificar_usuario(resultado["usuario"], resultado["contraseña"]):
        session["usuario"] = resultado["usuario"]
        return jsonify({"mensaje": "Inicio de sesión exitoso, ya puedes ver tus tareas."}), 200
    return jsonify({"error": "Usuario o contraseña incorrectos"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("usuario", None)
    return jsonify({"mensaje": "Sesión cerrada"}), 200


@app.route("/tareas", methods=["GET"])
def obtener_tareas():
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"error": "No autenticado"}), 401
    
    #Ejemplo de tareas
    tareas = [
        {"id": 1, "titulo": "Tarea 1", "descripcion": "Descripción de la tarea 1"},
        {"id": 2, "titulo": "Tarea 2", "descripcion": "Descripción de la tarea 2"},
    ]

    return render_template("bienvenida.html", usuario=usuario, tareas=tareas)


if __name__ == "__main__":
    app.run(debug=debug_mode, port=5000)