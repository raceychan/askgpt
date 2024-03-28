from pathlib import Path

import msgspec


class Config(msgspec.Struct):
    PROJECT_ROOT: Path = Path.cwd()
    MODEL_PATH: Path = PROJECT_ROOT / "src" / "models"
    MODEL_NAME: Path = Path("llama-2-7b.Q4_K_M")
    MODEL_PATH: Path = MODEL_PATH / f"{MODEL_NAME}.gguf"
