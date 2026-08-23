resource "google_storage_bucket" "artifacts" {
  name                        = "${var.project_id}-jobpilot-artifacts"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  versioning {
    enabled = true
  }
  depends_on                  = [google_project_service.services]
}
