import getpass

import requests

URL_BASE = "http://127.0.0.1:5000"
TIMEOUT = 5

sesion = requests.Session()


def mostrar_respuesta(respuesta):
    """Muestra el código de estado y el mensaje que devolvió el servidor."""
    try:
        datos = respuesta.json()
        mensaje = datos.get("mensaje") or datos.get("error") or datos
    except ValueError:
        mensaje = "Acceso correcto, página de bienvenida recibida." if respuesta.ok else respuesta.text
    estado = "OK" if respuesta.ok else "ERROR"
    print(f"[{estado} {respuesta.status_code}] {mensaje}")


def pedir_credenciales():
    usuario = input("Usuario: ").strip()
    contraseña = getpass.getpass("Contraseña: ")
    return usuario, contraseña


def enviar(metodo, ruta, **kwargs):
    """Hace la llamada HTTP y captura los errores de conexión."""
    try:
        respuesta = sesion.request(metodo, f"{URL_BASE}{ruta}", timeout=TIMEOUT, **kwargs)
        mostrar_respuesta(respuesta)
        return respuesta
    except requests.exceptions.ConnectionError:
        print("No se pudo conectar con el servidor. ¿Está corriendo servidor.py?")
    except requests.exceptions.Timeout:
        print("El servidor tardó demasiado en responder.")
    except requests.exceptions.RequestException as error:
        print(f"Error en la solicitud: {error}")
    return None


def registrar():
    usuario, contraseña = pedir_credenciales()
    enviar("POST", "/registro", json={"usuario": usuario, "contraseña": contraseña})


def iniciar_sesion():
    usuario, contraseña = pedir_credenciales()
    enviar("POST", "/login", json={"usuario": usuario, "contraseña": contraseña})


def ver_tareas():
    enviar("GET", "/tareas")


def cerrar_sesion():
    enviar("POST", "/logout")


def menu():
    opciones = {
        "1": ("Registrarse", registrar),
        "2": ("Iniciar sesión", iniciar_sesion),
        "3": ("Ver tareas", ver_tareas),
        "4": ("Cerrar sesión", cerrar_sesion),
    }

    while True:
        print("\n--- Cliente de tareas ---")
        for clave, (texto, _) in opciones.items():
            print(f"{clave}. {texto}")
        print("5. Salir")

        eleccion = input("Elegí una opción: ").strip()

        if eleccion == "5":
            print("¡Hasta luego!")
            break
        elif eleccion in opciones:
            opciones[eleccion][1]()
        else:
            print("Opción inválida, probá de nuevo.")


if __name__ == "__main__":
    menu()