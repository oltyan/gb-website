from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _compose() -> dict:
    return yaml.safe_load((ROOT / "docker-compose.yml").read_text())


def test_compose_project_name_is_pinned_to_existing_volume_prefix():
    # The live DB volume is gb-website-deploy_gb_data. Any other project
    # name makes compose create a fresh, empty volume.
    assert _compose()["name"] == "gb-website-deploy"


def test_compose_keeps_local_image_and_container_names():
    app = _compose()["services"]["app"]
    assert app["image"] == "gb-website:latest"
    assert app["container_name"] == "gb-website-app"
    assert "gb_data:/data" in app["volumes"]

JENKINSFILE = (ROOT / "Jenkinsfile.deploy").read_text()
ECR = "365647376064.dkr.ecr.us-east-1.amazonaws.com"


def test_jenkinsfile_polls_scm():
    assert "pollSCM('H/5 * * * *')" in JENKINSFILE


def test_jenkinsfile_pushes_sha_and_latest_to_ecr_after_tests():
    assert ECR in JENKINSFILE
    assert 'docker push "${ECR}:${SHA}"' in JENKINSFILE
    assert 'docker push "${ECR}:latest"' in JENKINSFILE
    assert JENKINSFILE.index("pytest") < JENKINSFILE.index("docker push")


def test_jenkinsfile_never_starts_containers_or_touches_secrets():
    # Jenkins runs on EC2; the site runs on mycelium.
    for forbidden in (
        "docker compose up",
        "secrets.env",
        "gb-website-secret-key",
        "gb-website-oidc-client-id",
        "gb-website-oidc-client-secret",
        "withAWS",
    ):
        assert forbidden not in JENKINSFILE, forbidden


def test_jenkinsfile_force_deploy_is_opt_in():
    assert "name: 'FORCE_DEPLOY'" in JENKINSFILE
    assert "defaultValue: false" in JENKINSFILE
    assert "when { expression { params.FORCE_DEPLOY } }" in JENKINSFILE
    assert "https://mycelium.musicalmycology.org/_deploy-trigger/gb-website" in JENKINSFILE
