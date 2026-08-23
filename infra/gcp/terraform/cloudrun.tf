locals {
  run_env = [
    { name = "JOBPILOT_ENV", value = "production" },
    { name = "JOBPILOT_CONFIG", value = "config/jobpilot.yaml" },
    { name = "JOBPILOT_ALLOW_LIVE_APPLY", value = "false" },
    { name = "LLM_PROVIDER", value = "heuristic" },
    { name = "GCS_BUCKET", value = google_storage_bucket.artifacts.name },
    { name = "GCS_PREFIX", value = "jobpilot" },
    { name = "GITHUB_USERNAME", value = "Dna072" },
    { name = "SMTP_PORT", value = "587" },
    { name = "EMAIL_PROVIDER", value = "smtp" },
  ]

  run_secrets = [
    { name = "DATABASE_URL", secret = google_secret_manager_secret.database_url.secret_id },
    { name = "JOBPILOT_OPS_TOKEN", secret = google_secret_manager_secret.ops_token.secret_id },
    { name = "SMTP_HOST", secret = google_secret_manager_secret.smtp_host.secret_id },
    { name = "SMTP_USERNAME", secret = google_secret_manager_secret.smtp_username.secret_id },
    { name = "SMTP_PASSWORD", secret = google_secret_manager_secret.smtp_password.secret_id },
    { name = "EMAIL_FROM", secret = google_secret_manager_secret.email_from.secret_id },
    { name = "EMAIL_TO", secret = google_secret_manager_secret.email_to.secret_id },
    { name = "GITHUB_TOKEN", secret = google_secret_manager_secret.github_token.secret_id },
  ]
}

resource "google_cloud_run_v2_service" "api" {
  name     = "jobpilot-api"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  depends_on = [
    google_project_service.services,
    google_secret_manager_secret_version.database_url,
    google_artifact_registry_repository.jobpilot,
  ]

  template {
    service_account                  = google_service_account.run.email
    max_instance_request_concurrency = 8
    timeout                          = "300s"
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    volumes {
      name = "cloudsql"
      cloud_sql_instance {
        instances = [google_sql_database_instance.jobpilot.connection_name]
      }
    }
    containers {
      image = var.api_image
      ports {
        container_port = 8080
      }
      resources {
        limits = { cpu = "1", memory = "1Gi" }
      }
      volume_mounts {
        name       = "cloudsql"
        mount_path = "/cloudsql"
      }
      dynamic "env" {
        for_each = local.run_env
        content {
          name  = env.value.name
          value = env.value.value
        }
      }
      dynamic "env" {
        for_each = local.run_secrets
        content {
          name = env.value.name
          value_source {
            secret_key_ref {
              secret  = env.value.secret
              version = "latest"
            }
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service" "web" {
  name     = "jobpilot-web"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"
  depends_on = [
    google_project_service.services,
    google_cloud_run_v2_service.api,
  ]

  template {
    service_account = google_service_account.run.email
    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }
    containers {
      image = var.web_image
      ports {
        container_port = 8080
      }
      resources {
        limits = { cpu = "1", memory = "512Mi" }
      }
      env {
        name  = "API_URL"
        value = google_cloud_run_v2_service.api.uri
      }
      env {
        name  = "NEXT_PUBLIC_API_URL"
        value = google_cloud_run_v2_service.api.uri
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "api_public" {
  count    = var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.api.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service_iam_member" "web_public" {
  count    = var.allow_unauthenticated ? 1 : 0
  name     = google_cloud_run_v2_service.web.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_job" "cycle" {
  name     = "jobpilot-cycle"
  location = var.region
  depends_on = [
    google_secret_manager_secret_version.database_url,
    google_artifact_registry_repository.jobpilot,
  ]

  template {
    template {
      service_account = google_service_account.run.email
      timeout         = "3600s"
      max_retries     = 1
      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.jobpilot.connection_name]
        }
      }
      containers {
        image   = var.api_image
        command = ["jobpilot"]
        args    = ["cycle"]
        resources {
          limits = { cpu = "1", memory = "1Gi" }
        }
        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
        dynamic "env" {
          for_each = local.run_env
          content {
            name  = env.value.name
            value = env.value.value
          }
        }
        dynamic "env" {
          for_each = local.run_secrets
          content {
            name = env.value.name
            value_source {
              secret_key_ref {
                secret  = env.value.secret
                version = "latest"
              }
            }
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_job" "watch" {
  name     = "jobpilot-watch"
  location = var.region
  depends_on = [
    google_secret_manager_secret_version.database_url,
    google_artifact_registry_repository.jobpilot,
  ]

  template {
    template {
      service_account = google_service_account.run.email
      timeout         = "600s"
      max_retries     = 1
      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.jobpilot.connection_name]
        }
      }
      containers {
        image   = var.api_image
        command = ["jobpilot"]
        args    = ["watch-repos"]
        resources {
          limits = { cpu = "1", memory = "512Mi" }
        }
        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
        dynamic "env" {
          for_each = local.run_env
          content {
            name  = env.value.name
            value = env.value.value
          }
        }
        dynamic "env" {
          for_each = local.run_secrets
          content {
            name = env.value.name
            value_source {
              secret_key_ref {
                secret  = env.value.secret
                version = "latest"
              }
            }
          }
        }
      }
    }
  }
}

resource "google_cloud_run_v2_job" "report" {
  name     = "jobpilot-report"
  location = var.region
  depends_on = [
    google_secret_manager_secret_version.database_url,
    google_artifact_registry_repository.jobpilot,
  ]

  template {
    template {
      service_account = google_service_account.run.email
      timeout         = "600s"
      max_retries     = 1
      volumes {
        name = "cloudsql"
        cloud_sql_instance {
          instances = [google_sql_database_instance.jobpilot.connection_name]
        }
      }
      containers {
        image   = var.api_image
        command = ["jobpilot"]
        args    = ["report"]
        resources {
          limits = { cpu = "1", memory = "512Mi" }
        }
        volume_mounts {
          name       = "cloudsql"
          mount_path = "/cloudsql"
        }
        dynamic "env" {
          for_each = local.run_env
          content {
            name  = env.value.name
            value = env.value.value
          }
        }
        dynamic "env" {
          for_each = local.run_secrets
          content {
            name = env.value.name
            value_source {
              secret_key_ref {
                secret  = env.value.secret
                version = "latest"
              }
            }
          }
        }
      }
    }
  }
}
