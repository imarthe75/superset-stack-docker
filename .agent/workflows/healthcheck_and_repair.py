from prefect import flow, task
import requests
import subprocess

@task(retries=2, retry_delay_seconds=5)
def check_service_health(url: str):
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return True

@task
def restart_service(service_name: str):
    print(f"Restarting {service_name} due to health check failure...")
    subprocess.run(["docker", "compose", "restart", service_name])

@flow(name="Aura Healthcheck and Auto-Repair")
def healthcheck_and_repair():
    services = {
        "superset": "http://superset:8088/health",
        "clickhouse-server": "http://clickhouse-server:8123/ping"
    }
    
    for name, url in services.items():
        try:
            check_service_health(url)
            print(f"{name} is healthy.")
        except Exception as e:
            print(f"{name} check failed: {e}")
            restart_service(name)

if __name__ == "__main__":
    healthcheck_and_repair()
