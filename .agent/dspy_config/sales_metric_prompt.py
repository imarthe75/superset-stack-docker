import dspy

class SalesMetricSignature(dspy.Signature):
    """Evalúa extraer métricas de ventas asegurando uso de dbt gold layer."""
    
    question = dspy.InputField(desc="Pregunta de negocio del usuario")
    context = dspy.InputField(desc="Esquema y golden sets de ventas desde ChromaDB")
    sql_query = dspy.OutputField(desc="Consulta SQL optimizada para ClickHouse contra aura_gold.fct_sales")

def get_sales_metric_prompt():
    return dspy.ChainOfThought(SalesMetricSignature)
