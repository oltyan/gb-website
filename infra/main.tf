# Retired 2026-11-13.
#
# This stack used to hold the grogblossoms.com apex -> www redirect:
# an ACM cert, a stub S3 bucket, a CloudFront function + distribution, and
# Route 53 apex A/AAAA alias records (PR #15).
#
# The zone is now served by Cloudflare DNS, so the Route 53 records are
# never queried and the distribution receives no traffic. The redirect is
# a Cloudflare proxied CNAME + Redirect Rule instead (see architecture.md,
# "DNS lives in Cloudflare").
#
# The resources were removed from this file so that the next
# `terraform apply` destroys what is still deployed. That apply has NOT
# been run as part of this change -- review the plan (it should be
# destroy-only) and run it by hand. Once state is empty, this directory
# can be deleted.
