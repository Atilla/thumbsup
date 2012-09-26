import logging

loglevels = ("INFO", "WARN", "WARNING", "ERROR", "CRITICAL", "FATAL", "DEBUG")


def phantomjs_to_log(line):
    loglevel = logging.DEBUG
    message  = None

    # Expect log output to be prefixed with LOGLEVEL:
    if ":" in line[:10]:
        level, message = line.strip().split(":", 1)
        level = level.upper()
        if level in loglevels:
            loglevel = getattr(logging, level)
            message = message.strip().decode("utf-8")
        else:
            message = line.strip()

    return loglevel, message


def on_phantom(pipe):
    """
    Callback for the phantomjs call
    """
    success = True
    for line in pipe.stdout:
        loglevel, message = phantomjs_to_log(line)
        if loglevel >= logging.ERROR:
            success = False
        if message:
            logging.log(loglevel, message)

    return success


def on_magic(pipe):
    """
    Callback for the imagemagic call
    """
    success = True
    for line in pipe.stdout:
        logging.error(line.strip())
        success = False
    if success:
        logging.info("Imagemagic resize success")

    return success
