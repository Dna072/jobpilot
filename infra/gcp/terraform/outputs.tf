output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}

output "web_url" {
  value = google_cloud_run_v2_service.web.uri
}

output "artifact_repo" {
  value = local.artifact_repo
}

output "sql_connection_name" {
  value = google_sql_database_instance.jobpilot.connection_name
}

output "artifacts_bucket" {
  value = google_storage_bucket.artifacts.name
}

output "ops_token_secret" {
  value = google_secret_manager_secret.ops_token.secret_id
}

output "region" {
  value = var.region
}
