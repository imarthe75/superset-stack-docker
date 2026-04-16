from prefect import flow, task
import subprocess

@task
def run_great_expectations():
    print("Running Great Expectations against aura_gold tables...")
    result = subprocess.run(["great_expectations", "checkpoint", "run", "aura_gold_checkpoint"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Quality gate failed: {result.stdout}")
    return result.stdout

@flow(name="Aura Validate Quality Gates")
def validate_quality_gates():
    print("Starting data quality validation...")
    try:
        report = run_great_expectations()
        print("Data quality validation passed.", report)
    except Exception as e:
        print(f"Data quality issue detected: {e}")

if __name__ == "__main__":
    validate_quality_gates()
