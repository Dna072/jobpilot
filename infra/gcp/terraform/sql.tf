resource "random_password" "db" {
  length  = 24
  special = false
}

resource "random_password" "ops" {
  length  = 32
  special = false
}

resource "google_sql_database_instance" "jobpilot" {
  name             = "jobpilot"
  database_version = "POSTGRES_16"
  region           = var.region
  depends_on       = [google_project_service.services]

  settings {
    # POSTGRES_16+ defaults to ENTERPRISE_PLUS, which rejects shared-core tiers.
    edition           = "ENTERPRISE"
    tier              = var.db_tier
    availability_type = "ZONAL"
    disk_size         = 10
    disk_autoresize   = true
    backup_configuration {
      enabled    = true
      start_time = "02:00"
    }
    ip_configuration {
      ipv4_enabled = true
    }
  }

  deletion_protection = var.deletion_protection
}

resource "google_sql_database" "jobpilot" {
  name     = "jobpilot"
  instance = google_sql_database_instance.jobpilot.name
}

resource "google_sql_user" "jobpilot" {
  name     = "jobpilot"
  instance = google_sql_database_instance.jobpilot.name
  password = random_password.db.result
}
