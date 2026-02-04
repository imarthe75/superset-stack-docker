# Guía Universal: Conectar Claude Desktop con Superset MCP

Esta guía funciona para **cualquier escenario**, ya sea que tengas todo en tu máquina o que Superset esté en un servidor en la nube.

## 1. Identifica tu Escenario

Elige la opción que describe tu situación:

* **Opción A (Remoto/Nube):** Claude Desktop está en tu PC (Mac/Windows) y Superset está en un servidor Linux (AWS, Azure, VPS, etc.). **(Lo más común)**.
* **Opción B (Local):** Tanto Claude Desktop como Superset están corriendo en la **misma** máquina.

---

## 2. Instalar Claude Desktop (Para ambos escenarios)

1. Descarga e instala Claude Desktop en tu ordenador personal: [https://claude.ai/download](https://claude.ai/download)
2. Inicia sesión con tu cuenta de Anthropic.

---

## 3. Conexión y Túneles

### Para Opción A (Servidor Remoto / Nube)

Como el servidor está lejos, necesitamos crear un "puente" (túnel SSH) seguro para que tu ordenador pueda hablar con el puerto `8010` del servidor como si fuera local.

**Mac / Linux (Terminal):**

```bash
# Opción 1: Con contraseña
ssh -L 8010:localhost:8010 usuario@tu-servidor-ip

# Opción 2: Con archivo de llave (.pem)
ssh -i /ruta/a/tu-llave.pem -L 8010:localhost:8010 usuario@tu-servidor-ip
```

**Windows (PowerShell):**

```powershell
ssh -i "C:\ruta\a\tu-llave.pem" -L 8010:localhost:8010 usuario@tu-servidor-ip
```

**Windows (PuTTY):**

1. **Connection > SSH > Tunnels**: Source `8010`, Destination `localhost:8010`, Add.
2. **Auth (Credenciales)**: Carga tu archivo `.ppk`.
3. **Session**: Conecta a la IP de tu servidor.

> [!IMPORTANT]
> **Debes mantener esta conexión SSH abierta** mientras uses Claude con Superset.

### Para Opción B (Todo Local)

No tienes que hacer nada en este paso. El puerto `8010` ya está disponible en tu máquina.

---

## 4. Configurar Claude Desktop

El archivo de configuración es el mismo para ambos casos, gracias al túnel SSH (en la Opción A) o a la red local (Opción B).

1. Ubica o crea el archivo de configuración:
    * **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
    * **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

    > [!WARNING]
    > **¡Importante!**
    > * Si no existe, créalo.
    > * El nombre debe ser **exactamente** `claude_desktop_config.json`.
    > * NO edites ningún archivo llamado simplemente `config.json`.

2. Pega el siguiente contenido:

```json
{
  "mcpServers": {
    "superset": {
      "url": "http://localhost:8010/sse"
    }
  }
}
```

1. Guarda el archivo y **reinicia totalmente** Claude Desktop.

---

## 5. Verificación

1. Abre Claude Desktop.
2. Busca el icono de "enchufe" (🔌) en la interfaz. Debería decir `superset` conectado.
3. Prueba: *"Muestra mis dashboards disponibles"*.
4. Si te responde con la lista, ¡felicidades! La conexión es exitosa y la auto-autenticación ha funcionado.
