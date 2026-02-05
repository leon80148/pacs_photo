from __future__ import annotations

import os
import sys
from pathlib import Path

import importlib
import uvicorn

from photo_pacs.settings import get_settings


def _app_home() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def main() -> None:
    app_home = _app_home()
    try:
        os.chdir(app_home)
    except OSError:
        pass

    settings = get_settings()
    app = importlib.import_module("photo_pacs.main").app
    uvicorn.run(app, host=settings.server_host, port=settings.server_port, log_config=None)


if __name__ == "__main__":
    main()
