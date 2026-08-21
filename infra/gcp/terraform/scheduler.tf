resource "google_cloud_scheduler_job" "cycle" {
  name        = "jobpilot-cycle"
  description = "Scout and process jobs every 6 hours"
  schedule    = "0 */6 * * *"
  time_zone   = "Europe/Stockholm"
  region      = var.scheduler_region
  depends_on  = [google_project_service.services, google_cloud_run_v2_job.cycle]

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${data.google_project.current.number}/jobs/${google_cloud_run_v2_job.cycle.name}:run"
    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
}

resource "google_cloud_scheduler_job" "watch" {
  name        = "jobpilot-watch"
  description = "Detect human-created GitHub repositories"
  schedule    = "*/15 * * * *"
  time_zone   = "Europe/Stockholm"
  region      = var.scheduler_region
  depends_on  = [google_project_service.services, google_cloud_run_v2_job.watch]

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${data.google_project.current.number}/jobs/${google_cloud_run_v2_job.watch.name}:run"
    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
}

resource "google_cloud_scheduler_job" "report" {
  name        = "jobpilot-weekly-report"
  description = "Weekly application performance email"
  schedule    = "0 7 * * 1"
  time_zone   = "Europe/Stockholm"
  region      = var.scheduler_region
  depends_on  = [google_project_service.services, google_cloud_run_v2_job.report]

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${data.google_project.current.number}/jobs/${google_cloud_run_v2_job.report.name}:run"
    oauth_token {
      service_account_email = google_service_account.scheduler.email
    }
  }
}
