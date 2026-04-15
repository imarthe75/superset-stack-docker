#!/usr/bin/env python3
"""
docker_tools.py — Herramientas MCP para control de Docker
==========================================================
Proyecto: Aura Intelligence Suite v8.0
Ubicación: .agent/MCP/docker_tools.py

Implementa el protocolo MCP (Model Context Protocol) para que el agente
pueda ejecutar operaciones Docker de forma segura y auditada.

SEGURIDAD:
    - Lista blanca de comandos permitidos (sin rm -rf, sin privileged)
    - Logs de auditoría de cada acción ejecutada
    - Timeout máximo de 60s por comando
    - Modo dry-run disponible para validación previa

USO:
    from .agent.MCP.docker_tools import DockerMCPTools
    tools = DockerMCPTools(dry_run=False)
    result = tools.service_status("superset")
    result = tools.restart_service("valkey")
    result = tools.get_logs("clickhouse-server", tail=50)
"""
from __future__ import annotations

import json
import logging
import subprocess
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Directorio del proyecto Aura
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Comandos permitidos (allowlist de seguridad)
ALLOWED_DOCKER_COMMANDS = {
    "ps", "logs", "inspect", "stats", "top", "exec",
    "compose", "info", "version", "network", "volume",
}

# Servicios que el agente puede reiniciar
RESTARTABLE_SERVICES = {
    "superset", "celery-worker", "celery-beat", "cube", "valkey",
    "nginx", "grafana", "prometheus", "prefect", "vanna-ai",
    "flowise", "superset-mcp", "dbt-runner",
}

# Servicios que requieren aprobación antes de reiniciar
SENSITIVE_SERVICES = {
    "postgres", "clickhouse-server", "peerdb", "keycloak",
}


@dataclass
class MCPResult:
    """Resultado estructurado de una operación MCP."""
    success: bool
    command: str
    output: str
    error: str = ""
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "command": self.command,
            "output": self.output,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        status = "✅" if self.success else "❌"
        return f"{status} [{self.duration_ms:.0f}ms] {self.command}\n{self.output or self.error}"


class DockerMCPTools:
    """
    Herramientas MCP para interacción con Docker.
    Todas las acciones son auditadas en el log del agente.
    """

    def __init__(self, dry_run: bool = False, compose_file: str | None = None) -> None:
        self.dry_run = dry_run
        self.compose_file = compose_file or str(PROJECT_ROOT / "docker-compose.yml")
        self._audit_log: list[MCPResult] = []

        if dry_run:
            logger.warning("🔵 DockerMCPTools en modo DRY-RUN. Ningún comando será ejecutado.")

    def _run(self, cmd: list[str], timeout: int = 60) -> MCPResult:
        """Ejecuta un comando Docker con auditoría y timeout."""
        cmd_str = " ".join(cmd)

        # Validar que el comando está en la allowlist
        if len(cmd) > 1 and cmd[0] == "docker" and cmd[1] not in ALLOWED_DOCKER_COMMANDS:
            return MCPResult(
                success=False,
                command=cmd_str,
                output="",
                error=f"Comando '{cmd[1]}' no está en la lista de comandos permitidos.",
            )

        logger.info(f"🐳 MCP Docker: {cmd_str}")

        if self.dry_run:
            return MCPResult(
                success=True,
                command=cmd_str,
                output=f"[DRY-RUN] Comando no ejecutado: {cmd_str}",
            )

        start = time.time()
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(PROJECT_ROOT),
            )
            duration = (time.time() - start) * 1000
            mcp_result = MCPResult(
                success=result.returncode == 0,
                command=cmd_str,
                output=result.stdout.strip(),
                error=result.stderr.strip() if result.returncode != 0 else "",
                duration_ms=duration,
            )
        except subprocess.TimeoutExpired:
            mcp_result = MCPResult(
                success=False,
                command=cmd_str,
                output="",
                error=f"Timeout ({timeout}s) ejecutando: {cmd_str}",
                duration_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            mcp_result = MCPResult(
                success=False,
                command=cmd_str,
                output="",
                error=str(e),
            )

        self._audit_log.append(mcp_result)
        return mcp_result

    # ── Herramientas de Observabilidad ──────────────────────────────────────

    def service_status(self, service: str | None = None) -> MCPResult:
        """Obtiene el estado de un servicio Docker Compose."""
        cmd = ["docker", "compose", "-f", self.compose_file, "ps"]
        if service:
            cmd.append(service)
        return self._run(cmd)

    def get_logs(self, service: str, tail: int = 100, since: str = "5m") -> MCPResult:
        """Obtiene los logs de un servicio."""
        return self._run([
            "docker", "compose", "-f", self.compose_file,
            "logs", "--tail", str(tail), "--since", since, service,
        ])

    def healthcheck_all(self) -> MCPResult:
        """Verifica el healthcheck de todos los servicios."""
        return self._run([
            "docker", "ps", "--format",
            "table {{.Names}}\t{{.Status}}\t{{.Ports}}",
        ])

    def get_resource_usage(self, service: str | None = None) -> MCPResult:
        """Obtiene el uso de CPU y RAM de los contenedores."""
        cmd = ["docker", "stats", "--no-stream", "--format",
               "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"]
        if service:
            cmd.append(service)
        return self._run(cmd)

    # ── Herramientas de Acción ───────────────────────────────────────────────

    def restart_service(self, service: str, force: bool = False) -> MCPResult:
        """
        Reinicia un servicio Docker Compose.

        Args:
            service: Nombre del servicio a reiniciar.
            force: Si True, permite reiniciar servicios sensibles.
        """
        if service in SENSITIVE_SERVICES and not force:
            return MCPResult(
                success=False,
                command=f"restart {service}",
                output="",
                error=(
                    f"'{service}' es un servicio sensible (base de datos/identidad). "
                    f"Usar force=True con aprobación explícita del usuario."
                ),
            )
        if service not in RESTARTABLE_SERVICES and not force:
            return MCPResult(
                success=False,
                command=f"restart {service}",
                output="",
                error=f"'{service}' no está en la lista de servicios reiniciables.",
            )
        return self._run([
            "docker", "compose", "-f", self.compose_file,
            "restart", service,
        ])

    def exec_in_service(self, service: str, command: list[str]) -> MCPResult:
        """Ejecuta un comando dentro de un contenedor (equivalente a docker exec)."""
        # Solo permitir comandos de consulta, no modificación
        safe_prefixes = ("clickhouse-client", "valkey-cli", "psql", "pg_isready",
                         "curl", "cat", "ls", "env", "echo", "dbt")
        if command and not any(command[0].startswith(p) for p in safe_prefixes):
            return MCPResult(
                success=False,
                command=f"exec {service} {' '.join(command)}",
                output="",
                error=f"Comando '{command[0]}' no está en la lista de comandos exec permitidos.",
            )
        return self._run([
            "docker", "compose", "-f", self.compose_file,
            "exec", service,
        ] + command)

    def validate_compose(self) -> MCPResult:
        """Valida la sintaxis del docker-compose.yml."""
        return self._run([
            "docker", "compose", "-f", self.compose_file, "config", "--quiet",
        ])

    # ── Utilidades ───────────────────────────────────────────────────────────

    def export_audit_log(self) -> str:
        """Exporta el log de auditoría como JSON."""
        return json.dumps([r.to_dict() for r in self._audit_log], indent=2)


# ── Uso rápido desde CLI ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    tools = DockerMCPTools(dry_run="--dry-run" in sys.argv)

    if "--status" in sys.argv:
        print(tools.healthcheck_all())
    elif "--resources" in sys.argv:
        print(tools.get_resource_usage())
    elif "--validate" in sys.argv:
        print(tools.validate_compose())
    else:
        print("Uso: python docker_tools.py [--status|--resources|--validate|--dry-run]")
