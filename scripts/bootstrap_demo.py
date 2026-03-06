import os
import requests
import json

SUPERSET_URL = "http://localhost:8088"
USERNAME = os.getenv("SUPERSET_ADMIN_USERNAME", "admin")
PASSWORD = os.getenv("SUPERSET_ADMIN_PASSWORD", "Qwertyuiopasd5$")

def get_token():
    resp = requests.post(f"{SUPERSET_URL}/api/v1/security/login", json={
        "username": USERNAME,
        "password": PASSWORD,
        "provider": "db",
        "refresh": True
    })
    return resp.json()["access_token"]

def create_db_connection(token):
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "allow_ctas": True,
        "allow_cvas": True,
        "database_name": "Sales Demo Database",
        "sqlalchemy_uri": "postgresql://superset:superset@postgres:5432/sales_data",
        "extra": json.dumps({"metadata_params": {}, "engine_params": {}, "metadata_cache_timeout": {}, "schemas_allowed_for_file_upload": []})
    }
    resp = requests.post(f"{SUPERSET_URL}/api/v1/database/", json=payload, headers=headers)
    if resp.status_code == 201:
        print("✅ Conexión a 'Sales Demo Database' creada en Superset.")
    else:
        print(f"⚠️ Nota: La base de datos ya existe o hubo un error: {resp.text}")

if __name__ == "__main__":
    try:
        token = get_token()
        create_db_connection(token)
    except Exception as e:
        print(f"❌ Error conectando a Superset: {e}")
