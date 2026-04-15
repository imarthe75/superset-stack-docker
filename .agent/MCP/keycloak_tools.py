#!/usr/bin/env python3
"""
keycloak_tools.py — Herramientas MCP para gestión de Keycloak
==============================================================
Proyecto: Aura Intelligence Suite v8.0
Ubicación: .agent/MCP/keycloak_tools.py

Permite al agente verificar y gestionar el Identity Provider Keycloak:
- Verificar que el realm 'superset' existe y tiene el cliente configurado
- Listar usuarios y roles
- Validar tokens OIDC

SEGURIDAD:
    - Solo operaciones GET/LIST (no crear/borrar usuarios)
    - Credenciales desde variables de entorno
    - Las contraseñas nunca aparecen en los resultados
"""
from __future__ import annotations

import os
from typing import Any

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class KeycloakMCPTools:
    """Herramientas MCP para verificación de Keycloak OIDC."""

    def __init__(
        self,
        base_url: str | None = None,
        realm: str | None = None,
        admin_user: str | None = None,
        admin_password: str | None = None,
    ) -> None:
        self.base_url = (base_url or os.getenv("KEYCLOAK_URL", "http://keycloak:8080")).rstrip("/")
        self.realm = realm or os.getenv("OIDC_OPENID_REALM", "superset")
        self.admin_user = admin_user or os.getenv("KEYCLOAK_ADMIN", "admin")
        self.admin_password = admin_password or os.getenv("KEYCLOAK_ADMIN_PASSWORD", "")
        self._token: str | None = None

    def _get_admin_token(self) -> str:
        """Obtiene un token de administración de Keycloak."""
        if not HAS_REQUESTS:
            raise RuntimeError("requests no instalado: pip install requests")
        resp = requests.post(
            f"{self.base_url}/auth/realms/master/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "admin-cli",
                "username": self.admin_user,
                "password": self.admin_password,
            },
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _get_headers(self) -> dict[str, str]:
        if self._token is None:
            self._token = self._get_admin_token()
        return {"Authorization": f"Bearer {self._token}"}

    def check_health(self) -> dict[str, Any]:
        """Verifica que Keycloak responde."""
        try:
            resp = requests.get(
                f"{self.base_url}/auth/realms/{self.realm}",
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "healthy",
                    "realm": data.get("realm"),
                    "public_key_available": bool(data.get("public_key")),
                }
            return {"status": "error", "http_code": resp.status_code}
        except Exception as e:
            return {"status": "unreachable", "error": str(e)}

    def get_realm_info(self) -> dict[str, Any]:
        """Obtiene información del realm configurado."""
        resp = requests.get(
            f"{self.base_url}/auth/admin/realms/{self.realm}",
            headers=self._get_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        # Filtrar datos sensibles
        return {
            "realm": data.get("realm"),
            "enabled": data.get("enabled"),
            "login_theme": data.get("loginTheme"),
            "access_token_lifespan": data.get("accessTokenLifespan"),
            "sso_session_max_lifespan": data.get("ssoSessionMaxLifespan"),
        }

    def get_clients(self) -> list[dict[str, Any]]:
        """Lista los clientes OIDC del realm."""
        resp = requests.get(
            f"{self.base_url}/auth/admin/realms/{self.realm}/clients",
            headers=self._get_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return [
            {
                "clientId": c.get("clientId"),
                "enabled": c.get("enabled"),
                "protocol": c.get("protocol"),
                "publicClient": c.get("publicClient"),
                "redirectUris": c.get("redirectUris", [])[:3],
            }
            for c in resp.json()
            if not c.get("clientId", "").startswith("realm-management")
        ]

    def get_user_count(self) -> int:
        """Retorna el número de usuarios en el realm."""
        resp = requests.get(
            f"{self.base_url}/auth/admin/realms/{self.realm}/users/count",
            headers=self._get_headers(),
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()


# ── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import json, sys
    tools = KeycloakMCPTools()

    if "--health" in sys.argv:
        print(json.dumps(tools.check_health(), indent=2))
    elif "--realm" in sys.argv:
        print(json.dumps(tools.get_realm_info(), indent=2))
    elif "--clients" in sys.argv:
        print(json.dumps(tools.get_clients(), indent=2))
    elif "--users" in sys.argv:
        print(f"Usuarios en realm '{tools.realm}': {tools.get_user_count()}")
    else:
        print("Uso: python keycloak_tools.py [--health|--realm|--clients|--users]")
