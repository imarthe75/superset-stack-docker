import os
import requests
import json
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import JSONResponse
import uvicorn

# Configuration
SUPERSET_BASE_URL = os.getenv("SUPERSET_BASE_URL", "http://superset:8088")
SUPERSET_USERNAME = os.getenv("SUPERSET_USERNAME", "admin")
SUPERSET_PASSWORD = os.getenv("SUPERSET_PASSWORD", "Qwertyuiopasd5$")

# Global access token
_access_token = None

def get_token():
    global _access_token
    if _access_token:
        return _access_token
    
    url = f"{SUPERSET_BASE_URL}/api/v1/security/login"
    payload = {
        "username": SUPERSET_USERNAME,
        "password": SUPERSET_PASSWORD,
        "provider": "db",
        "refresh": True
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    _access_token = resp.json()["access_token"]
    return _access_token

# Define MCP server
server = Server("Superset MCP")

@server.list_tools()
async def list_tools():
    return [
        {
            "name": "list_dashboards",
            "description": "List all available dashboards in Superset",
            "inputSchema": {"type": "object", "properties": {}}
        },
        {
            "name": "get_dashboard_info",
            "description": "Get detailed info and charts from a specific dashboard",
            "inputSchema": {
                "type": "object", 
                "properties": {
                    "dashboard_id": {"type": "integer", "description": "The ID of the dashboard"}
                },
                "required": ["dashboard_id"]
            }
        },
        {
            "name": "list_datasets",
            "description": "List all datasets",
            "inputSchema": {"type": "object", "properties": {}}
        }
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    token = get_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    if name == "list_dashboards":
        url = f"{SUPERSET_BASE_URL}/api/v1/dashboard/"
        resp = requests.get(url, headers=headers)
        data = resp.json().get("result", [])
        return [{"type": "text", "text": f"Found {len(data)} dashboards:\n" + "\n".join([f"- [{d['id']}] {d['dashboard_title']}" for d in data])}]

    elif name == "get_dashboard_info":
        db_id = arguments["dashboard_id"]
        url = f"{SUPERSET_BASE_URL}/api/v1/dashboard/{db_id}"
        resp = requests.get(url, headers=headers)
        res = resp.json().get("result", {})
        return [{"type": "text", "text": f"Dashboard: {res.get('dashboard_title')}\nMetadata: {json.dumps(res.get('json_metadata'), indent=2)}"}]

    elif name == "list_datasets":
        url = f"{SUPERSET_BASE_URL}/api/v1/dataset/"
        resp = requests.get(url, headers=headers)
        data = resp.json().get("result", [])
        return [{"type": "text", "text": f"Found {len(data)} datasets:\n" + "\n".join([f"- [{d['id']}] {d['table_name']}" for d in data])}]

    return [{"type": "text", "text": f"Tool {name} not found"}]

# SSE Setup (FastAPI-like with Starlette)
sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

async def handle_messages(request):
    await sse.handle_post_message(request.scope, request.receive, request._send)

app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse),
        Route("/messages", endpoint=handle_messages, methods=["POST"]),
    ]
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("MCP_PORT", 8010)))
