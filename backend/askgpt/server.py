import uvicorn

from askgpt.feat.app import app_factory
from askgpt.domain import config
from askgpt.helpers.file import relative_path

if __name__ == "__main__":
    config.sys_finetune()
    uvicorn.run(
        f"{relative_path(__file__)}:{app_factory.__name__}",
        host="0.0.0.0",
        port=5000,
        factory=True,
        reload=True,
        reload_excludes=["test_*.py", "conftest.py"],
        log_config=None,
    )
