import pandas as pd
import mysql.connector
import json

# 1. Configuración de conexión a tu Base de Datos
db_config = {
    'host': 'localhost',
    'user': 'tu_usuario',
    'password': 'tu_password',
    'database': 'gestor_practicas'
}

def conectar_db():
    return mysql.connector.connect(**db_config)

# 2. Función para cargar el CSV (Alumnos)
def cargar_csv(ruta_archivo):
    conn = conectar_db()
    cursor = conn.cursor()
    df = pd.read_csv(ruta_archivo)
    
    for _, fila in df.iterrows():
        # Primero insertamos en 'usuarios' para obtener el ID
        sql_user = "INSERT INTO usuarios (nombre, email, contrasena, rol) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql_user, (fila['nombre'], fila['email'], fila['contrasena'], fila['rol']))
        usuario_id = cursor.lastrowid
        
        # Luego insertamos en 'alumnos' usando ese ID
        sql_alumno = "INSERT INTO alumnos (usuario_id, ciclo_id, telefono) VALUES (%s, %s, %s)"
        cursor.execute(sql_alumno, (usuario_id, fila['ciclo_id'], fila['telefono']))
        
    conn.commit()
    print("CSV cargado con éxito.")
    cursor.close()
    conn.close()

# 3. Función para cargar la API (Empresas)
def cargar_api(ruta_json):
    conn = conectar_db()
    cursor = conn.cursor()
    
    with open(ruta_json, 'r') as f:
        datos_empresa = json.load(f)
        
    for empresa in datos_empresa:
        sql = """INSERT INTO empresas (nombre, direccion, web, email, telefono) 
                 VALUES (%s, %s, %s, %s, %s)"""
        valores = (empresa['nombre'], empresa['direccion'], empresa['web'], empresa['email'], empresa['telefono'])
        cursor.execute(sql, valores)
        
    conn.commit()
    print("Datos de API (JSON) cargados con éxito.")
    cursor.close()
    conn.close()

# Ejecución
if __name__ == "__main__":
    # Asegúrate de que los archivos existan en la misma carpeta
    cargar_csv('datos_alumnos.csv')
    cargar_api('config.json')
