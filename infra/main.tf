locals {
  apex = "grogblossoms.com"
  www  = "https://www.grogblossoms.com"
}

# ---------------------------------------------------------------------------
# Route 53 zone — already exists, we only write records into it.
# ---------------------------------------------------------------------------

data "aws_route53_zone" "grogblossoms" {
  name         = local.apex
  private_zone = false
}

# ---------------------------------------------------------------------------
# ACM cert for the apex. CloudFront requires certs in us-east-1 (handled by
# the provider). Route 53 is in the same account so validation is automatic.
# ---------------------------------------------------------------------------

resource "aws_acm_certificate" "apex" {
  domain_name       = local.apex
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.apex.domain_validation_options :
    dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  }

  zone_id         = data.aws_route53_zone.grogblossoms.zone_id
  name            = each.value.name
  type            = each.value.type
  ttl             = 60
  records         = [each.value.record]
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "apex" {
  certificate_arn         = aws_acm_certificate.apex.arn
  validation_record_fqdns = [for r in aws_route53_record.cert_validation : r.fqdn]
}

# ---------------------------------------------------------------------------
# Stub S3 bucket — CloudFront requires an origin, but the viewer-request
# function below intercepts every request and returns a redirect before
# CloudFront ever contacts the origin.
# ---------------------------------------------------------------------------

resource "aws_s3_bucket" "redirect_stub" {
  bucket = "grogblossoms-apex-redirect-stub"
}

resource "aws_s3_bucket_public_access_block" "redirect_stub" {
  bucket                  = aws_s3_bucket.redirect_stub.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_origin_access_control" "redirect_stub" {
  name                              = "grogblossoms-redirect-stub"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_s3_bucket_policy" "redirect_stub" {
  bucket = aws_s3_bucket.redirect_stub.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.redirect_stub.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.apex_redirect.arn
        }
      }
    }]
  })
}

# ---------------------------------------------------------------------------
# CloudFront Function — 301 every request to https://www.grogblossoms.com,
# preserving the URI path. Runs at viewer-request before the origin is
# contacted, so the stub bucket is never actually fetched.
# ---------------------------------------------------------------------------

resource "aws_cloudfront_function" "apex_redirect" {
  name    = "grogblossoms-apex-redirect"
  runtime = "cloudfront-js-2.0"
  publish = true
  code    = <<-EOF
    function handler(event) {
      return {
        statusCode: 301,
        statusDescription: "Moved Permanently",
        headers: {
          location: { value: "https://www.grogblossoms.com" + event.request.uri }
        }
      };
    }
  EOF
}

# ---------------------------------------------------------------------------
# CloudFront distribution — apex only; www continues through the Cloudflare
# tunnel unchanged.
# ---------------------------------------------------------------------------

resource "aws_cloudfront_distribution" "apex_redirect" {
  enabled         = true
  is_ipv6_enabled = true
  aliases         = [local.apex]
  price_class     = "PriceClass_100"
  comment         = "grogblossoms.com apex → www redirect"

  origin {
    domain_name              = aws_s3_bucket.redirect_stub.bucket_regional_domain_name
    origin_id                = "stub"
    origin_access_control_id = aws_cloudfront_origin_access_control.redirect_stub.id
  }

  default_cache_behavior {
    target_origin_id       = "stub"
    viewer_protocol_policy = "allow-all"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    # CachingDisabled — no point caching a redirect that never varies.
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"

    function_association {
      event_type   = "viewer-request"
      function_arn = aws_cloudfront_function.apex_redirect.arn
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate_validation.apex.certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}

# ---------------------------------------------------------------------------
# Route 53 — apex A-record aliased to the CloudFront distribution.
# The www CNAME (manual entry pointing to the Cloudflare tunnel) is
# intentionally not managed here.
# ---------------------------------------------------------------------------

resource "aws_route53_record" "apex" {
  zone_id = data.aws_route53_zone.grogblossoms.zone_id
  name    = local.apex
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.apex_redirect.domain_name
    zone_id                = "Z2FDTNDATAQYW2" # CloudFront's fixed hosted-zone id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "apex_aaaa" {
  zone_id = data.aws_route53_zone.grogblossoms.zone_id
  name    = local.apex
  type    = "AAAA"

  alias {
    name                   = aws_cloudfront_distribution.apex_redirect.domain_name
    zone_id                = "Z2FDTNDATAQYW2"
    evaluate_target_health = false
  }
}
