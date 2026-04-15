from prefect import flow, task
import subprocess
import os

# --- CONFIGURACIÓN ---
DBT_PROJECT_DIR = "/opt/prefect/dbt_aura"
DBT_PROFILES_DIR = DBT_PROJECT_DIR

@task(retries=2, retry_delay_seconds=60)
def run_dbt_task(command: str):
    """
    Ejecuta comandos dbt y captura la salida.
    """
    print(f"Ejecutando: dbt {command}...")
    
    # Construimos el comando completo
    full_cmd = [
        "dbt", 
        command, 
        "--project-dir", DBT_PROJECT_DIR, 
        "--profiles-dir", DBT_PROFILES_DIR,
        "--target", "dev"
    ]
    
    # Ejecución
    result = subprocess.run(
        full_cmd, 
        capture_output=True, 
        text=True,
        env=os.environ.copy()
    )
    
    if result.returncode == 0:
        print(f"✅ dbt {command} exitoso.")
        print(result.stdout)
        return True
    else:
        print(f"❌ Error en dbt {command}:")
        print(result.stderr)
        print(result.stdout)
        raise Exception(f"Falla en comando dbt {command}")

@flow(name="Aura MDS — dbt Transformation Pipeline")
def dbt_aura_flow():
    """
    Pipeline de transformación Medallón: Bronze -> Silver -> Gold
    """
    # 1. Validar conexión
    run_dbt_task("debug")
    
    # 2. Correr modelos (Bronze a Gold)
    # dbt-clickhouse usará los modelos definidos en models/
    run_dbt_task("run")
    
    # 3. Ejecutar tests de calidad
    run_dbt_task("test")
    
    return "MDS Pipeline Completado"

if __name__ == "__main__":
    dbt_aura_flow()
