import os
try:
    from vanna.chromadb import ChromaDB_VectorStore
    from vanna.openai import OpenAI_Chat
    from vanna.remote import VannaDefault
except ImportError:
    from vanna.legacy.chromadb.chromadb_vector import ChromaDB_VectorStore
    from vanna.legacy.openai.openai_chat import OpenAI_Chat
    from vanna.legacy.remote import VannaDefault
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2

# Basic Setup
# For a full local setup, we'd use Ollama, but let's assume OpenAI/Anthropic/VannaCloud for the demo
# Or use Vanna's built-in remote LLM if no key is provided
class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        OpenAI_Chat.__init__(self, config=config)

vn = MyVanna(config={
    'api_key': os.getenv('OPENAI_API_KEY', 'sk-None'),
    'model': 'gpt-4o-mini',
    'path': './vanna_db'
})

# Database Connection
def connect_db():
    use_cube = os.getenv('CUBE_SQL_HOST') is not None
    host = os.getenv('CUBE_SQL_HOST', os.getenv('POSTGRES_HOST', 'postgres'))
    port = int(os.getenv('CUBE_SQL_PORT', 15432) if use_cube else 5432)
    user = os.getenv('CUBE_SQL_USER', os.getenv('POSTGRES_USER', 'superset'))
    password = os.getenv('CUBE_SQL_PASSWORD', os.getenv('POSTGRES_PASSWORD', 'superset'))
    dbname = os.getenv('POSTGRES_DB', 'sales_data')
    
    print(f"Vanna connecting to Database: {host}:{port}")
    vn.connect_to_postgres(
        host=host,
        dbname=dbname,
        user=user,
        password=password,
        port=port
    )

app = Flask(__name__)
CORS(app)

@app.route('/', methods=['GET'])
def health():
    return jsonify({"status": "Aura Vanna AI Service is running", "endpoints": ["/ask", "/train/schema", "/train/golden_sets"]})

@app.route('/train/golden_sets', methods=['POST'])
def train_golden_sets():
    import glob
    import json
    try:
        connect_db()
        # Find all JSON files in /app/golden_sets (mounted via Docker)
        files = glob.glob("/app/golden_sets/*.json")
        count = 0
        for f in files:
            with open(f, 'r') as file:
                data = json.load(file)
                for item in data:
                    if 'query' in item and 'expected_sql' in item:
                        vn.train(question=item['query'], sql=item['expected_sql'])
                        count += 1
        return jsonify({"status": f"Golden sets trained, {count} queries added."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        connect_db()
        sql = vn.generate_sql(question)
        df = vn.run_sql(sql)
        # Convert df to JSON
        results = df.to_dict(orient='records')
        return jsonify({
            "sql": sql,
            "results": results
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/train/schema', methods=['POST'])
def train_schema():
    # Helper to train on the database schema
    try:
        connect_db()
        df_information_schema = vn.run_sql("SELECT * FROM information_schema.tables WHERE table_schema = 'public'")
        vn.train(ddl=df_information_schema.to_string())
        return jsonify({"status": "Schema training samples added"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8011)
