import linecache
import sys

from utils import logger


def print_exception(exit=False):
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    line = line.strip()

    msg = "EXCEPTION IN ({}, LINE: {}, CODE: {}): {} {}".format(
        filename, lineno, line, exc_type, exc_obj
    )
    logger.error(msg)

    if exit:
        sys.exit(1)

    return msg
