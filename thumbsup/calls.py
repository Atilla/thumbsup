import logging


def on_phantom(pipe):
    """
    Callback for the phantomjs call
    """
    success = True
    for line in pipe.stdout:
        # Expect log output to be prefixed with LOGLEVEL:
        if ":" in line[:10]:
            level, message = line.strip().split(":", 1)
            level = level.upper()
            line = line.strip()
            logging.log(getattr(logging, level, 20),
                        message.decode("utf-8"))
            if level in ("ERROR", "CRITICAL"):
                success = False
        else:  # Default to info logging
            logging.info(line)

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
