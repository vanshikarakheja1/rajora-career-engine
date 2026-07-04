import sys
import os
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


if __name__ == "__main__":
    try:
        import uvicorn
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "uvicorn is not installed in the active Python environment. "
            "Activate the project virtual environment or run: python -m pip install -r requirements.txt"
        ) from exc

    host = os.getenv("CAREER_ENGINE_HOST", "127.0.0.1")
    port = int(os.getenv("CAREER_ENGINE_PORT", "8000"))
    reload = os.getenv("CAREER_ENGINE_RELOAD", "true").strip().lower() == "true"
    uvicorn.run("career_engine.api.main:app", host=host, port=port, reload=reload)
