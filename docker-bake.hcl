group "default" {
  targets = ["ubuntu-ci"]
}

target "ubuntu-ci" {
  context    = "."
  dockerfile = "images/ubuntu-ci/Dockerfile"
  platforms  = ["linux/amd64"]
  tags       = ["whitekiwi/ubuntu-ci:local"]
}
