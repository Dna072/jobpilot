resource "google_service_account" "run" {
  account_id   = "jobpilot-run"
  display_name = "JobPilot Cloud Run"
}

resource "google_service_account" "scheduler" {
  account_id   = "jobpilot-scheduler"
  display_name = "JobPilot Cloud Scheduler"
}

resource "google_service_account" "builder" {
  account_id   = "jobpilot-builder"
  display_name = "JobPilot Cloud Build"
}

resource "google_project_iam_member" "run_sql" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.run.email}"
}

resource "google_project_iam_member" "run_secret" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.run.email}"
}

resource "google_storage_bucket_iam_member" "run_objects" {
  bucket = google_storage_bucket.artifacts.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.run.email}"
}

resource "google_cloud_run_v2_job_iam_member" "scheduler_invoker" {
  for_each = toset(["jobpilot-cycle", "jobpilot-watch", "jobpilot-report"])
  name     = each.value
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
  depends_on = [
    google_cloud_run_v2_job.cycle,
    google_cloud_run_v2_job.watch,
    google_cloud_run_v2_job.report,
  ]
}

resource "google_project_iam_member" "scheduler_job_runner" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}

resource "google_artifact_registry_repository_iam_member" "run_pull" {
  location   = google_artifact_registry_repository.jobpilot.location
  repository = google_artifact_registry_repository.jobpilot.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${google_service_account.run.email}"
}

resource "google_artifact_registry_repository_iam_member" "cloudbuild_write" {
  location   = google_artifact_registry_repository.jobpilot.location
  repository = google_artifact_registry_repository.jobpilot.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${data.google_project.current.number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "builder_logs" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.builder.email}"
}
