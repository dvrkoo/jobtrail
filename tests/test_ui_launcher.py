from pathlib import Path

from sqlmodel import Session, select

from jobtrail.db import engine, init_db
from jobtrail.models import Application
from jobtrail.services.ui import build_streamlit_launch, prepare_demo


def test_build_streamlit_launch_args() -> None:
    launch = build_streamlit_launch(
        port=8502,
        no_browser=True,
        demo=True,
        config_dir=Path("/tmp/cfg"),
        data_dir=Path("/tmp/data"),
    )
    assert launch.args[:4][-2:] == ["streamlit", "run"]
    assert "--server.port" in launch.args
    assert "8502" in launch.args
    assert launch.env["JOBTRAIL_UI_DEMO"] == "1"
    assert launch.env["JOBTRAIL_CONFIG_DIR"] == "/tmp/cfg"


def test_prepare_demo_loads_sample(tmp_path, monkeypatch) -> None:
    config_dir = tmp_path / "config"
    data_dir = tmp_path / "data"
    prepare_demo(config_dir, data_dir, Path("examples/sample_gmail_messages.json"))
    monkeypatch.setenv("JOBTRAIL_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("JOBTRAIL_DATA_DIR", str(data_dir))
    init_db()
    with Session(engine()) as db:
        assert len(db.exec(select(Application)).all()) == 6
