variable "REGISTRY" {
  default = "ghcr.io"
}

variable "REPO" {
  default = "aretedriver/agent-lint"
}

group "default" {
  targets = ["agent-lint"]
}

target "agent-lint" {
  dockerfile = "Dockerfile"
  tags = [
    "${REGISTRY}/${REPO}:latest",
    "${REGISTRY}/${REPO}:{{ .Version }}",
  ]
  platforms = ["linux/amd64", "linux/arm64"]
}
