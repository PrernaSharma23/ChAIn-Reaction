import logging

# Create logger
log = logging.getLogger("impact_analysis")
log.setLevel(logging.INFO)

# Avoid duplicate handlers if reloaded
if not log.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s] [%(filename)s:%(lineno)d] %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(formatter)

    log.addHandler(console_handler)
