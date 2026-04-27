# tests/test_importacion_empresas.py
import requests
import json

BASE_URL = "http://localhost:8000/api"

# ────────────────────────────────────────
# FIXTURES (datos de prueba)
# ────────────────────────────────────────

EMPRESA_VALIDA = {
    "nombre": "Tech Solutions S.L.",
    "direccion": "Calle Falsa 123",
    "web": "www.techsolutions.com",
    "email": "info@tech.com",
    "telefono": "912344556"
}

EMPRESA_EMAIL_INVALIDO = {
    "nombre": "Empresa Rota",
    "direccion": "Calle Test 1",
    "web": "www.test.com",
    "email": "esto-no-es-un-email",   # ← inválido a propósito
    "telefono": "912344556"
}

EMPRESA_SIN_NOMBRE = {
    "direccion": "Calle Test 1",
    "web": "www.test.com",
    "email": "info@test.com",
    "telefono": "912344556"
    # ← falta "nombre" a propósito
}

EMPRESA_TELEFONO_INVALIDO = {
    "nombre": "Empresa Rota 2",
    "direccion": "Calle Test 2",
    "web": "www.test.com",
    "email": "info@test.com",
    "telefono": "noesuntelefono"       # ← inválido a propósito
}

# ────────────────────────────────────────
# TESTS DE IMPORTACIÓN
# ────────────────────────────────────────

def test_json_valido_importa_dos_empresas():
    """El JSON original con 2 empresas debe importarse correctamente"""
    empresas = [EMPRESA_VALIDA, {
        "nombre": "Innovatech",
        "direccion": "Avenida de la Paz 5",
        "web": "www.innovatech.es",
        "email": "hr@innovatech.es",
        "telefono": "934556677"
    }]

    respuesta = requests.post(
        f"{BASE_URL}/importar/empresas",
        json=empresas
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["importadas"] == 2

def test_empresa_con_email_invalido_es_rechazada():
    """Un email sin @ no debe importarse"""
    respuesta = requests.post(
        f"{BASE_URL}/importar/empresas",
        json=[EMPRESA_EMAIL_INVALIDO]
    )

    assert respuesta.status_code == 400
    assert "email" in respuesta.json()["error"].lower()

def test_empresa_sin_nombre_es_rechazada():
    """Una empresa sin nombre no debe importarse"""
    respuesta = requests.post(
        f"{BASE_URL}/importar/empresas",
        json=[EMPRESA_SIN_NOMBRE]
    )

    assert respuesta.status_code == 400

def test_empresa_con_telefono_invalido_es_rechazada():
    """Un teléfono que no son números debe rechazarse"""
    respuesta = requests.post(
        f"{BASE_URL}/importar/empresas",
        json=[EMPRESA_TELEFONO_INVALIDO]
    )

    assert respuesta.status_code == 400

def test_lista_vacia_es_rechazada():
    """Mandar un JSON vacío no debe importar nada ni romper el servidor"""
    respuesta = requests.post(
        f"{BASE_URL}/importar/empresas",
        json=[]
    )

    assert respuesta.status_code == 400

def test_importacion_duplicada_no_duplica_empresas():
    """Importar el mismo JSON dos veces no debe crear empresas duplicadas"""
    empresas = [EMPRESA_VALIDA]

    requests.post(f"{BASE_URL}/importar/empresas", json=empresas)
    respuesta = requests.post(f"{BASE_URL}/importar/empresas", json=empresas)

    assert respuesta.json().get("duplicadas", 0) >= 1

def test_mandar_csv_en_vez_de_json_es_rechazado():
    """Si mandan un CSV donde se espera JSON, debe devolver error claro"""
    respuesta = requests.post(
        f"{BASE_URL}/importar/empresas",
        data="nombre,email\nEmpresa,info@test.com",  # texto plano, no JSON
        headers={"Content-Type": "text/plain"}
    )

    assert respuesta.status_code in [400, 415]  # 415 = Unsupported Media Type