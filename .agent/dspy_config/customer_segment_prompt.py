import dspy

class CustomerSegmentSignature(dspy.Signature):
    """Evalúa extraer segmentos de clientes asegurando uso de dbt gold layer."""
    
    question = dspy.InputField(desc="Pregunta de negocio del usuario sobre clientes")
    context = dspy.InputField(desc="Esquema y golden sets de clientes desde ChromaDB")
    sql_query = dspy.OutputField(desc="Consulta SQL optimizada para ClickHouse contra aura_gold.dim_customer")

def get_customer_segment_prompt():
    return dspy.ChainOfThought(CustomerSegmentSignature)
