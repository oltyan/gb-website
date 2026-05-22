terraform {
  backend "s3" {
    bucket         = "musicalmycology-tfstate"
    key            = "grogblossoms/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "musicalmycology-tflock"
    encrypt        = true
  }
}
