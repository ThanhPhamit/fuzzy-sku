terraform {
  backend "s3" {
    bucket       = "fuzzy-sku-poc-tfstates-fty"
    region       = "ap-northeast-3"
    key          = "osaka-prod/terraform.tfstate"
    profile      = "welfan-lg-mfa"
    use_lockfile = true
  }
}
