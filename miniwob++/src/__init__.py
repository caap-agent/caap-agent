import logging

def get_logger(logger_name:str):
    # Logger
    logger = logging.getLogger(logger_name)  # Create a logger object
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)  # Set the logging level to INFO

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        console_formatter = logging.Formatter("%(message)s")
        ch.setFormatter(console_formatter)

        logger.addHandler(ch)
        logger.propagate = False  # don't let root logger handle the log message

    return logger
