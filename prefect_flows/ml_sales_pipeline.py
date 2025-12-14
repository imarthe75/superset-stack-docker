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
DB_URL = "postgresql+psycopg2://superset:superset@postgres:5432/sales_data" 
# En docker-compose.yml definimos CUBEJS_API_SECRET como SECRET_KEY
CUBEJS_API_TOKEN = os.environ.get("CUBEJS_API_SECRET", "SUPER_SECRETO_CAMBIAR_ESTO_EN_PROD") 
# Importante: Cube Store/API corre en el puerto 4000 del servicio 'cube'
CUBEJS_REFRESH_URL = "http://cube:4000/cubejs-api/v1/pre-aggregations/refresh"

# ----------------------------------------------------
# Tareas Atómicas
# ----------------------------------------------------

@task(retries=3, retry_delay_seconds=30)
def sembrar_datos_historicos():
    """Crea y puebla la tabla ventas_historicas si está vacía."""
    print("Verificando tabla de ventas históricas...")
    engine = create_engine(DB_URL)
    
    # Datos iniciales (Semilla)
    data = {
        'historico_mes': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'ventas_reales': [100, 150, 120, 200, 210, 250, 240, 300, 320, 350]
    }
    df_semilla = pd.DataFrame(data)

    # Verificamos si la tabla existe y tiene datos
    try:
        # Intentamos leer para ver si existe
        existing_data = pd.read_sql("SELECT count(*) as cnt FROM ventas_historicas", engine)
        count = existing_data['cnt'][0]
        if count > 0:
            print(f"La tabla ventas_historicas ya existe y tiene {count} registros. Se usarán estos datos.")
            return True
    except:
        print("La tabla no existe o está vacía. Creando y sembrando datos iniciales...")

    # Si llegamos aquí, escribimos la semilla
    try:
        df_semilla.to_sql('ventas_historicas', engine, if_exists='append', index=False)
        print("Datos históricos sembrados correctamente.")
    except Exception as e:
        print(f"Error al sembrar datos: {e}")
        # Intentamos hacer create replace si falló append por no existir tabla
        df_semilla.to_sql('ventas_historicas', engine, if_exists='replace', index=False)
        print("Tabla creada y datos sembrados.")
    
    return True

@task(retries=3, retry_delay_seconds=30)
def verificar_datos_fuente():
    """Simula la verificación de datos en PostgreSQL."""
    print("Verificando integridad de los datos fuente en PostgreSQL...")
    engine = create_engine(DB_URL)
    try:
        df = pd.read_sql("SELECT * FROM ventas_historicas LIMIT 5", engine)
        if df.empty:
            print("Alerta: Tabla ventas_historicas vacía.")
            return False
        return True
    except Exception as e:
        print(f"Error verificando fuente: {e}")
        return False

@task
def entrenar_y_predecir_ventas():
    """Ejecuta el modelo de ML usando datos de DB y y guarda predicciones."""
    print("Iniciando entrenamiento y predicción...")
    
    engine = create_engine(DB_URL)

    # 1. Extracción desde DB
    print("Leyendo datos históricos desde sales_data...")
    df = pd.read_sql("SELECT * FROM ventas_historicas", engine)
    
    if df.empty:
        raise ValueError("No hay datos para entrenar.")

    X = df[['historico_mes']]
    y = df['ventas_reales']
    
    # 2. Entrenamiento
    print(f"Entrenando modelo con {len(df)} registros...")
    model = LinearRegression()
    model.fit(X, y)
    
    # Predecir el siguiente mes (Max mes + 1)
    siguiente_mes = df['historico_mes'].max() + 1
    mes_a_predecir = pd.DataFrame({'historico_mes': [siguiente_mes]})
    prediccion = model.predict(mes_a_predecir)[0]
    
    results_df = pd.DataFrame({
        'fecha_prediccion': [datetime.now().strftime('%Y-%m-%d')],
        'mes_simulado': [siguiente_mes],
        'prediccion_ventas': [round(prediccion, 2)],
        'modelo_version': ['v1.1-dynamic']
    })
    
    # 3. Carga de Resultados en PostgreSQL
    try:
        TABLE_NAME = 'ml_prediccion_ventas' 
        results_df.to_sql(TABLE_NAME, engine, if_exists='replace', index=False)
        print(f"Predicción para el mes {siguiente_mes}: {round(prediccion, 2)}")
        print(f"Resultados guardados en {TABLE_NAME}.")
    except Exception as e:
        print(f"Error al cargar en la base de datos: {e}")
        raise 
    
    return True

@task
def refrescar_cubo_ventas(ml_status):
    """Llama a la API de Cube.js para forzar el refresco de los pre-agregados."""
    if not ml_status:
        raise ValueError("La tarea de ML no terminó exitosamente.")
        
    print(f"Enviando solicitud de refresco a Cube.js en {CUBEJS_REFRESH_URL}...")
    
    payload = {
        "cubes": ["MlPrediccionVentas"], 
        "force": True
    }
    
    try:
        response = requests.post(CUBEJS_REFRESH_URL, json=payload, timeout=60)
        print(f"Cube.js respondió: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Advertencia: No se pudo contactar a Cube.js: {e}")
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
    
    # 0. Sembrar (Garantizar datos)
    datos_sembrados = sembrar_datos_historicos()

    if datos_sembrados:
        # 1. Verificar
        datos_listos = verificar_datos_fuente()

        # 2. ML y Carga
        if datos_listos:
            ml_completado = entrenar_y_predecir_ventas()
            
            # 3. Refresco Cube.js
            cubo_fresco = refrescar_cubo_ventas(ml_completado)
            
            # 4. Notificación
            notificar_exito(cubo_fresco)
        else:
            print("Flujo abortado: Falló verificación de datos.")
    else:
        print("Flujo abortado: Falló sembrado de datos.")

if __name__ == "__main__":
    ml_bi_flow()
