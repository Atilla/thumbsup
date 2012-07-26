import hashlib
from base64 import urlsafe_b64encode
import os

# Just for fun right now
_le_sel = "sdhf1ascibl"


def _simple_digest(*args):
    """
    Simply returns the SHA1 hexdigest of all args
    """
    result = hashlib.sha1(_le_sel)
    for x in args:
        result.update(x.encode("utf-8"))
    return urlsafe_b64encode(result.digest()).rstrip("=")


def consistent_two_level(slots):
    """
    Returns a naive consistent hashing function over 'slots'
    """
    # The use of hashing is a tad too extensive here
    # but I just want something slightly more elaborate for now
    def _digest(*args):
        """
        Returns a path of the form:
        /slotname/args[0]hash/argshash
        """
        item = _simple_digest(*args)
        x = [(_simple_digest(n, item), n) for n in slots]
        return os.path.join(min(x)[1], _simple_digest(args[0]), item)
    return _digest


def get_subs(path):
    """
    Returns all subfolders in the given path
    """
    subs = [x for x in os.listdir(path)
            if os.path.isdir(os.path.join(path, x))]
    return subs
