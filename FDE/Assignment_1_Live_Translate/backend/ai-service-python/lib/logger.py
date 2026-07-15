"""
lib/logger.py — structured JSON logging  (PROVIDED — you may extend)
====================================================================
Emits one JSON object per line to stdout AND to ai-service.log. Any keyword
you pass via `extra=` is merged into the line, so `log.info("translate",
extra={"cached": True, "latencyMs": 4})` becomes a greppable structured event.

    tail -f ai-service.log | grep translate

Set LOG_FILE to another path to move the file, or to an empty string to drop it
and log to stdout only — which is what a container wants, since the runtime
captures and rotates stdout for you.
"""
import json
import logging
import os
from datetime import datetime, timezone

LOG_FILE_DEFAULT = "ai-service.log"
_RESERVED = set(logging.makeLogRecord({}).__dict__.keys()) | {"message", "asctime"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "event": record.getMessage(),
        }
        for k, v in record.__dict__.items():
            if k not in _RESERVED and not k.startswith("_"):
                payload[k] = v
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:  # already configured
        return logger
    logger.setLevel(logging.INFO)
    fmt = JsonFormatter()

    stream = logging.StreamHandler()
    stream.setFormatter(fmt)
    logger.addHandler(stream)

    # Read here, not at import: app.py imports this module before it calls
    # load_dotenv(), so a module-level getenv would bind first and silently
    # ignore a LOG_FILE set in .env. get_logger() runs after that call, which is
    # what makes this behave like TRANSLATION_DB_PATH rather than merely look
    # like it. Empty means stdout only.
    log_file = os.getenv("LOG_FILE", LOG_FILE_DEFAULT)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    logger.propagate = False
    return logger
