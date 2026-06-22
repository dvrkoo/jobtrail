from jobtrail.config import AppConfig, config_exists, load_config, save_config, update_config
from jobtrail.cli import first_startup_needed


def test_config_creation_loading_and_update(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(tmp_path / "data"))
    assert not config_exists()
    saved = save_config(AppConfig(display_name="Nic", motivational_tone="funny"))
    assert saved.created_at
    assert config_exists()
    assert load_config().display_name == "Nic"
    assert update_config(ghosting_threshold_days=45).ghosting_threshold_days == 45


def test_first_startup_detection(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(tmp_path / "config"))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(tmp_path / "data"))
    assert first_startup_needed()
