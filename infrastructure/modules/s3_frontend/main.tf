resource "random_uuid" "s3_bucket_postfix_uuid" {}

resource "aws_s3_bucket" "frontend" {
  bucket = "${var.app_name}-frontend-${substr(random_uuid.s3_bucket_postfix_uuid.result, 0, 3)}"

  tags = merge(
    var.tags,
    {
      "Name" = "${var.app_name}-frontend-${substr(random_uuid.s3_bucket_postfix_uuid.result, 0, 3)}"
    }
  )
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.frontend.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_ownership_controls" "this" {
  bucket = aws_s3_bucket.frontend.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_cloudfront_origin_access_control" "main" {
  name                              = "${var.app_name}-cf-oac-for-frontend-s3"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_secretsmanager_secret" "basic_auth" {
  count       = var.create_cloudfront_function ? 1 : 0
  name_prefix = "${var.app_name}-CDN-basic-auth"
  tags = merge(
    var.tags,
    {
      "Name" = "${var.app_name}-CDN-basic-auth"
    }
  )
}

resource "aws_secretsmanager_secret_version" "basic_auth_version" {
  count     = var.create_cloudfront_function ? 1 : 0
  secret_id = aws_secretsmanager_secret.basic_auth[count.index].id
  secret_string = jsonencode({
    username = var.app_name
    password = var.basic_auth_password
  })

  depends_on = [aws_secretsmanager_secret.basic_auth]
}

resource "aws_cloudfront_function" "basic_auth" {
  count   = var.create_cloudfront_function ? 1 : 0
  name    = "${var.app_name}-basic-auth"
  runtime = "cloudfront-js-2.0"
  comment = "Basic Auth"
  publish = true
  code = templatefile(
    "${path.module}/basic_auth.js",
    {
      authString = base64encode("${jsondecode(aws_secretsmanager_secret_version.basic_auth_version[count.index].secret_string).username}:${jsondecode(aws_secretsmanager_secret_version.basic_auth_version[count.index].secret_string).password}")
    }
  )
  depends_on = [aws_secretsmanager_secret_version.basic_auth_version]
}

resource "aws_cloudfront_distribution" "frontend" {
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = aws_s3_bucket.frontend.id
    origin_access_control_id = aws_cloudfront_origin_access_control.main.id
  }

  aliases     = [var.domain]
  enabled     = true
  price_class = var.price_class

  default_root_object = "index.html"

  # react の場合、root path 以外の path にアクセスした場合に 403 が返ってくるので、
  # それを index.html にリダイレクトする
  custom_error_response {
    error_caching_min_ttl = 0
    error_code            = 403
    response_code         = 200
    response_page_path    = "/"
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = aws_s3_bucket.frontend.id

    forwarded_values {
      query_string = false
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0

    dynamic "function_association" {
      for_each = var.create_cloudfront_function ? [aws_cloudfront_function.basic_auth] : []
      content {
        event_type   = "viewer-request"
        function_arn = function_association.value[0].arn
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
      locations        = []
    }
  }
  viewer_certificate {
    acm_certificate_arn = var.acm_certificate_arn
    ssl_support_method  = "sni-only"
  }

  tags = merge(
    var.tags,
    {
      "Name" = "${var.app_name}-frontend-cloudfront"
    }
  )
}

data "aws_iam_policy_document" "frontend" {
  statement {
    sid    = "Allow CloudFront"
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }
    actions = [
      "s3:GetObject"
    ]

    resources = [
      "${aws_s3_bucket.frontend.arn}/*"
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:SourceArn"
      values   = [aws_cloudfront_distribution.frontend.arn]
    }
  }
}

resource "aws_s3_bucket_policy" "this" {
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend.json
}


resource "aws_route53_record" "app_domain_dns_record" {
  name    = var.domain
  type    = "A"
  zone_id = var.route_53_zone_id

  alias {
    evaluate_target_health = false
    name                   = aws_cloudfront_distribution.frontend.domain_name
    zone_id                = aws_cloudfront_distribution.frontend.hosted_zone_id
  }
}
