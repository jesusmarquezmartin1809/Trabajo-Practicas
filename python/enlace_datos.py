import pandas as pd
import mysql.connector
import json
import re
import bcrypt
from dotenv import load_dotenv
import os

# 1. Cargar credenciales desde .env (nunca hardcodear en el código)
load_dotenv()

db_config = {
    'host':     os.getenv('DB_HOST'),
    'user':     os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME'),
}


# ── Helpers de validación ────────────────────────────────────────────────────

def email_valido(email: str) -> bool:
    patron = r'^[\w\.\+\-]+@[\w\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(patron, str(email).strip()))

def telefono_valido(telefono: str) -> bool:
    # Acepta formatos españoles: 9 dígitos, opcionalmente con +34 o 0034
    patron = r'^(\+34|0034)?[6789]\d{8}$'
    return bool(re.match(patron, str(telefono).strip().replace(' ', '')))

def hashear_contrasena(contrasena: str) -> str:
    """Genera un hash bcrypt de la contraseña en texto plano."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(contrasena.encode('utf-8'), salt).decode('utf-8')


# ── Conexión ─────────────────────────────────────────────────────────────────

def conectar_db():
    return mysql.connector.connect(**db_config)


# ── Carga de alumnos desde CSV ────────────────────────────────────────────────

def cargar_csv(ruta_archivo: str):
    conn = conectar_db()
    cursor = conn.cursor()
    df = pd.read_csv(ruta_archivo)

    insertados = 0
    errores    = 0

    for idx, fila in df.iterrows():
        fila_num = idx + 2  # +2 porque idx arranca en 0 y hay cabecera

        try:
            # — Validaciones de formato —
            if not email_valido(fila['email']):
                print(f"[Fila {fila_num}] Email inválido: {fila['email']} — omitida.")
                errores += 1
                continue

            if not telefono_valido(str(fila['telefono'])):
                print(f"[Fila {fila_num}] Teléfono inválido: {fila['telefono']} — omitida.")
                errores += 1
                continue

            # — Detección de duplicados por email —
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (fila['email'],))
            if cursor.fetchone():
                print(f"[Fila {fila_num}] Email duplicado: {fila['email']} — omitida.")
                errores += 1
                continue

            # — Detección de duplicados por DNI —
            cursor.execute("SELECT id FROM alumnos WHERE dni = %s", (fila['dni'],))
            if cursor.fetchone():
                print(f"[Fila {fila_num}] DNI duplicado: {fila['dni']} — omitida.")
                errores += 1
                continue

            # — Contraseña: se genera una temporal y se hashea.
            #   En producción usa un flujo de invitación/reset en lugar de
            #   enviar contraseñas por CSV. —
            contrasena_temporal = os.urandom(12).hex()          # 24 chars hex
            contrasena_hash     = hashear_contrasena(contrasena_temporal)

            # — El rol SIEMPRE es 'alumno', independientemente del CSV —
            rol = 'alumno'

            # — Inserción en 'usuarios' —
            sql_user = """
                INSERT INTO usuarios (nombre, email, contrasena, rol)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_user, (fila['nombre'], fila['email'], contrasena_hash, rol))
            usuario_id = cursor.lastrowid

            # — Inserción en 'alumnos' —
            sql_alumno = """
                INSERT INTO alumnos (usuario_id, ciclo_id, telefono, dni)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql_alumno, (usuario_id, fila['ciclo_id'], fila['telefono'], fila['dni']))

            conn.commit()
            insertados += 1
            print(f"[Fila {fila_num}] Alumno '{fila['nombre']}' insertado correctamente.")

        except Exception as e:
            conn.rollback()
            print(f"[Fila {fila_num}] Error inesperado: {e} — omitida.")
            errores += 1

    print(f"\nResumen CSV → Insertados: {insertados} | Omitidos/Errores: {errores}")
    cursor.close()
    conn.close()


# ── Carga de empresas desde JSON ──────────────────────────────────────────────

def cargar_api(ruta_json: str):
    conn = conectar_db()
    cursor = conn.cursor()

    with open(ruta_json, 'r', encoding='utf-8') as f:
        datos_empresa = json.load(f)

    insertadas = 0
    errores    = 0

    for empresa in datos_empresa:
        nombre = empresa.get('nombre', '—')

        try:
            # — Validaciones de formato —
            if not email_valido(empresa.get('email', '')):
                print(f"[Empresa '{nombre}'] Email inválido — omitida.")
                errores += 1
                continue

            if not telefono_valido(str(empresa.get('telefono', ''))):
                print(f"[Empresa '{nombre}'] Teléfono inválido — omitida.")
                errores += 1
                continue

            # — Detección de duplicados por CIF —
            cursor.execute("SELECT id FROM empresas WHERE cif = %s", (empresa['cif'],))
            if cursor.fetchone():
                print(f"[Empresa '{nombre}'] CIF duplicado: {empresa['cif']} — omitida.")
                errores += 1
                continue

            # — Inserción principal —
            sql_empresa = """
                INSERT INTO empresas (cif, nombre, direccion, web, email, telefono, persona_contacto)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            valores_empresa = (
                empresa['cif'],
                nombre,
                empresa.get('direccion'),
                empresa.get('web'),
                empresa.get('email'),
                empresa.get('telefono'),
                empresa.get('persona_contacto'),
            )
            cursor.execute(sql_empresa, valores_empresa)
            empresa_id = cursor.lastrowid

            # — Responsable legal —
            rl = empresa.get('responsable_legal', {})
            if rl:
                sql_rl = """
                    INSERT INTO responsables_legales (empresa_id, nombre, dni)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql_rl, (empresa_id, rl.get('nombre'), rl.get('dni')))

            # — Tutores laborales —
            for tutor in empresa.get('tutores_laborales', []):
                sql_tutor = """
                    INSERT INTO tutores_laborales (empresa_id, nombre, dni, telefono)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql_tutor, (
                    empresa_id,
                    tutor.get('nombre'),
                    tutor.get('dni'),
                    tutor.get('telefono'),
                ))

            # — Plazas por ciclo —
            for plaza in empresa.get('plazas', []):
                sql_plaza = """
                    INSERT INTO plazas (empresa_id, ciclo_id, num_alumnos)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(sql_plaza, (
                    empresa_id,
                    plaza.get('ciclo_id'),
                    plaza.get('num_alumnos'),
                ))

            conn.commit()
            insertadas += 1
            print(f"[Empresa '{nombre}'] Insertada correctamente.")

        except Exception as e:
            conn.rollback()
            print(f"[Empresa '{nombre}'] Error inesperado: {e} — omitida.")
            errores += 1

    print(f"\nResumen JSON → Insertadas: {insertadas} | Omitidas/Errores: {errores}")
    cursor.close()
    conn.close()


# ── Punto de entrada ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    cargar_csv('datos_alumnos.csv')
    cargar_api('config.json')
