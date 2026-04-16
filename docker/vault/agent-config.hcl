pid_file = "/var/run/vault-agent.pid"

vault {
  address = "http://vault:8200"
}

auto_auth {
  method "approle" {
    mount_path = "auth/approle"
    config = {
      role_id_file_path = "/vault/role_id"
      secret_id_file_path = "/vault/secret_id"
      remove_secret_id_file_after_reading = false
    }
  }
}

template {
  source      = "/vault/templates/env.ctmpl"
  destination = "/vault/secrets/.env"
}
