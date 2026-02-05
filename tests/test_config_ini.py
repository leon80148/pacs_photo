from __future__ import annotations

from photo_pacs.settings import Settings


def test_ini_overrides_dotenv(tmp_path, monkeypatch):
    ini_path = tmp_path / "config.ini"
    ini_path.write_text(
        "[photo_pacs]\n"
        "pacs_backend=mock\n"
        "PHOTO_PACS_PACS_HOST=10.0.0.9\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("PHOTO_PACS_CONFIG", str(ini_path))

    settings = Settings()

    assert settings.pacs_backend == "mock"
    assert settings.pacs_host == "10.0.0.9"


def test_env_overrides_ini(tmp_path, monkeypatch):
    ini_path = tmp_path / "config.ini"
    ini_path.write_text(
        "[photo_pacs]\n"
        "pacs_port=11112\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("PHOTO_PACS_CONFIG", str(ini_path))
    monkeypatch.setenv("PHOTO_PACS_PACS_PORT", "22222")

    settings = Settings()

    assert settings.pacs_port == 22222
