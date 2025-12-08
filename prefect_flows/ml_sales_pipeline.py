from prefect import flow, task
import pandas as pd
from sklearn.linear_model import LinearRegression
from sqlalchemy import create_engine
from datetime import datetime
import requests
import time
import os

# --- CONFIGURACIÓN ---
# Usamos las variables definidas en la red de Docker
DB_URL = "postgresql+psycopg2://superset:superset@postgres:5432/superset" 
# En docker-compose.yml definimos CUBEJS_API_SECRET como SECRET_KEY
CUBEJS_API_TOKEN = os.environ.get("CUBEJS_API_SECRET", "SUPER_SECRETO_CAMBIAR_ESTO_EN_PROD") 
# Importante: Cube Store/API corre en el puerto 4000 del servicio 'cube'
CUBEJS_REFRESH_URL = "http://cube:4000/cubejs-api/v1/pre-aggregations/refresh"

# ----------------------------------------------------
# Tareas Atómicas
# ----------------------------------------------------

@task(retries=3, retry_delay_seconds=30)
def verificar_datos_fuente():
    """Simula la verificación de datos en PostgreSQL."""
    print("Verificando integridad de los datos fuente en PostgreSQL...")
    time.sleep(1)
    return True

@task
def entrenar_y_predecir_ventas():
    """Ejecuta el modelo de ML y guarda las predicciones en PostgreSQL."""
    print("Iniciando entrenamiento y predicción...")
    
    # 1. Extracción y Preparación (Simulación)
    data = {
        'historico_mes': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'ventas_reales': [100, 150, 120, 200, 210, 250, 240, 300, 320, 350]
    }
    df = pd.DataFrame(data)
    X = df[['historico_mes']]
    y = df['ventas_reales']
    
    # 2. Entrenamiento, Predicción y Creación del Resultado
    model = LinearRegression()
    model.fit(X, y)
    mes_a_predecir = pd.DataFrame({'historico_mes': [11]})
    prediccion = model.predict(mes_a_predecir)[0]
    
    results_df = pd.DataFrame({
        'fecha_prediccion': [datetime.now().strftime('%Y-%m-%d')],
        'mes_simulado': [11],
        'prediccion_ventas': [round(prediccion, 2)],
        'modelo_version': ['v1.0']
    })
    
    # 3. Carga de Resultados en PostgreSQL
    try:
        engine = create_engine(DB_URL)
        TABLE_NAME = 'ml_prediccion_ventas' 
        results_df.to_sql(TABLE_NAME, engine, if_exists='replace', index=False)
        print(f"Predicciones cargadas en la tabla {TABLE_NAME}.")
    except Exception as e:
        print(f"Error al cargar en la base de datos: {e}")
        raise # Fuerza el fallo del flujo si la carga falla
    
    return True

@task
def refrescar_cubo_ventas(ml_status):
    """Llama a la API de Cube.js para forzar el refresco de los pre-agregados."""
    if not ml_status:
        raise ValueError("La tarea de ML no terminó exitosamente.")
        
    # Nota: En un entorno real, necesitas generar un JWT válido usando el API Secret.
    # Para simplificar en dev, si CUBEJS_DEV_MODE=true, Cube.js podría no requerir auth fuerte 
    # o podrías usar el secret directo dependiendo de la configuración. 
    # Pero lo correcto es un JWT. Aquí asumiremos que pasamos el token generado o el secret si se permite.
    # Para efectos de esta PoC simple, enviaremos un header de Auth genérico simulado si no hay generador JWT a mano,
    # o imprimiremos el aviso.
    
    print(f"Enviando solicitud de refresco a Cube.js en {CUBEJS_REFRESH_URL}...")
    
    # En producción real: import jwt; token = jwt.encode({}, CUBEJS_API_TOKEN)
    # Aquí simulamos el request con el framework.
    payload = {
        "cubes": ["MlPrediccionVentas"], # Nombre del Cubo que crearemos
        "force": True
    }
    
    try:
        # Nota: La API de refresh suele requerir auth. 
        # Si falla por 403, el usuario deberá implementar generación de JWT.
        response = requests.post(CUBEJS_REFRESH_URL, json=payload, timeout=60)
        print(f"Cube.js respondió: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Advertencia: No se pudo contactar a Cube.js (normal si no está listo aún): {e}")
        # No fallamos el flujo completo por esto en la PoC
        pass

    return True

@task
def notificar_exito(cube_status):
    """Notificación final de que el pipeline ha terminado."""
    print("¡Éxito! El pipeline de ML y BI ha terminado. Datos y predicciones frescos.")
    return "Pipeline completado"

# ----------------------------------------------------
# Flujo Principal
# ----------------------------------------------------

@flow(name="Pipeline ML y Refresco BI")
def ml_bi_flow():
    """El flujo completo que conecta la verificación, ML, Cube.js y la notificación."""
    
    # 1. Verificar
    datos_listos = verificar_datos_fuente()

    # 2. ML y Carga (depende de la verificación)
    if datos_listos:
        ml_completado = entrenar_y_predecir_ventas()
        
        # 3. Refresco Cube.js (depende del ML)
        cubo_fresco = refrescar_cubo_ventas(ml_completado)
        
        # 4. Notificación
        notificar_exito(cubo_fresco)
    else:
        print("Flujo abortado por fallas en la verificación de datos fuente.")

if __name__ == "__main__":
    ml_bi_flow()
