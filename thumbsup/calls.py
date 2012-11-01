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


def call_phantom(path, script, host, destination, view_size, ua_string, ip):
    callargs = []
    callargs.append(path)
    callargs.append(script)
    callargs.append(host)
    callargs.append(destination)
    x, y = view_size.split('x')
    callargs.append(x)
    callargs.append(y)
    callargs.append("'%s'" % ua_string)
    callargs.append(ip)
    return callargs


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


def call_imagic_resize(destination, thumb_size):
    callargs = []
    callargs.append("convert")
    callargs.append(destination)
    callargs.append("-filter")
    callargs.append("Lanczos")
    callargs.append("-thumbnail")
    callargs.append(thumb_size)
    callargs.append(destination)
    return callargs


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
