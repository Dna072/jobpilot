terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  type        = string
  description = "GCP project ID"
}

variable "region" {
  type        = string
  description = "GCP region. europe-north1 is Finland (closest Nordic region to Stockholm)."
  default     = "europe-north1"
}

variable "api_image" {
  type        = string
  description = "Artifact Registry image for the API / worker jobs"
}

variable "web_image" {
  type        = string
  description = "Artifact Registry image for the Next.js dashboard"
}

variable "db_tier" {
  type        = string
  default     = "db-f1-micro"
  description = "Cloud SQL tier. db-f1-micro is the cheapest shared instance."
}

variable "deletion_protection" {
  type    = bool
  default = true
}

variable "allow_unauthenticated" {
  type        = bool
  default     = true
  description = "If true, the dashboard/API are publicly reachable. Ops routes still require JOBPILOT_OPS_TOKEN."
}

variable "scheduler_region" {
  type        = string
  description = "Cloud Scheduler is not in every region. europe-west1 (Belgium) is the usual EU home."
  default     = "europe-west1"
}

locals {
  connection_name = google_sql_database_instance.jobpilot.connection_name
  database_url = format(
    "postgresql+psycopg://jobpilot:%s@/jobpilot?host=/cloudsql/%s",
    urlencode(random_password.db.result),
    local.connection_name,
  )
  artifact_repo = "${var.region}-docker.pkg.dev/${var.project_id}/jobpilot"
}

data "google_project" "current" {
  project_id = var.project_id
}
