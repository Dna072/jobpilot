resource "google_secret_manager_secret" "database_url" {
  secret_id = "jobpilot-database-url"
  replication {
    auto {}
  }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "database_url" {
  secret      = google_secret_manager_secret.database_url.id
  secret_data = local.database_url
}

resource "google_secret_manager_secret" "ops_token" {
  secret_id = "jobpilot-ops-token"
  replication {
    auto {}
  }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "ops_token" {
  secret      = google_secret_manager_secret.ops_token.id
  secret_data = random_password.ops.result
}

resource "google_secret_manager_secret" "smtp_host" {
  secret_id = "jobpilot-smtp-host"
  replication { auto {} }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret" "smtp_username" {
  secret_id = "jobpilot-smtp-username"
  replication { auto {} }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret" "smtp_password" {
  secret_id = "jobpilot-smtp-password"
  replication { auto {} }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret" "email_from" {
  secret_id = "jobpilot-email-from"
  replication { auto {} }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret" "email_to" {
  secret_id = "jobpilot-email-to"
  replication { auto {} }
  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret" "github_token" {
  secret_id = "jobpilot-github-token"
  replication { auto {} }
  depends_on = [google_project_service.services]
}
