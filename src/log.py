import logging


def get_logger(name: str, module: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(f"{module}.{name}")
    logger.setLevel(level)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(
        "[{asctime}] {name:<32s} {levelname:<8s} - {message}", style="{"
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger
