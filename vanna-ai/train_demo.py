import os
import requests
import json
import time

VANNA_URL = "http://localhost:8011"

def train():
    print("Esperando a que Vanna esté listo...")
    # Intento simple de verificar si el servicio está arriba
    for _ in range(10):
        try:
            # Endpoint de entrenamiento que creamos antes
            resp = requests.post(f"{VANNA_URL}/train/schema")
            if resp.status_code == 200:
                print("✅ Vanna ha sido entrenado con el nuevo esquema de ventas.")
                return
        except:
            pass
        time.sleep(5)
    print("❌ No se pudo conectar con Vanna para el entrenamiento.")

if __name__ == "__main__":
    train()
