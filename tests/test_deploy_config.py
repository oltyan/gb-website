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
