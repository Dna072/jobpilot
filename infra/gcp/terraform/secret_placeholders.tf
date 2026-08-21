resource "google_secret_manager_secret_version" "smtp_placeholders" {
  for_each = {
    host     = google_secret_manager_secret.smtp_host.id
    username = google_secret_manager_secret.smtp_username.id
    password = google_secret_manager_secret.smtp_password.id
    from     = google_secret_manager_secret.email_from.id
    to       = google_secret_manager_secret.email_to.id
    github   = google_secret_manager_secret.github_token.id
  }
  secret                 = each.value
  secret_data            = "unset"
  deletion_policy        = "ABANDON"
  lifecycle { ignore_changes = [secret_data] }
}
