variable "image_tag" {
  type        = string
  default     = "latest"
  description = "Docker image's tag (e.g. latest, dev, qa, prd, ...)"
}

variable "disable_old_ecs" {
  type        = string
  default     = "on"
  description = "Deregister all previous ECS Task Definitions automatically. Valid values are ('on', 'off')"
  validation {
    condition     = contains(["on", "off"], var.disable_old_ecs)
    error_message = "Valid values for var: disable_old_ecs are ('on', 'off')"
  }
}

variable "update_ecs" {
  type        = string
  default     = "off"
  description = "Updates ECS Task Definition's image automatically. Valid values are ('on', 'off')"
  validation {
    condition     = contains(["on", "off"], var.update_ecs)
    error_message = "Valid values for var: update_ecs are ('on', 'off')"
  }
}

variable "update_lambda" {
  type        = string
  default     = "off"
  description = "Updates Lambda's image automatically. Valid values are ('on', 'off')"
  validation {
    condition     = contains(["on", "off"], var.update_lambda)
    error_message = "Valid values for var: update_lambda are ('on', 'off')"
  }
}

variable "event_state" {
  type        = string
  default     = "ENABLED"
  description = "EventBridge rule's state. Valid values are ('ENABLED', 'DISABLED')"
  validation {
    condition     = contains(["ENABLED", "DISABLED"], var.event_state)
    error_message = "Valid values for var: event_state are ('ENABLED', 'DISABLED')"
  }
}

variable "prefix_module" {
  type        = string
  default     = "dkr-update"
  description = "Prefix for naming AWS resources of this module"
}

variable "prefix_ecs" {
  type        = string
  default     = "ecs-"
  description = "Prefix of IAM roles that will be passed for ECS update"
}

variable "retention" {
  type        = number
  default     = 30
  description = "Lambda logs retention in days"
}

variable "concurrents" {
  type        = number
  default     = 4
  description = "Reserved concurrent Lambda executions"
}

variable "runtime" {
  type        = string
  default     = "python3.14"
  description = "Lambda runtime version"
}

variable "tags" {
  type        = map(string)
  description = "Tags that will be applied to the module's resources"
}
