import hashlib
import os


def _simple_digest(*args):
    """
    Simply returns the SHA1 hexdigest of all args
    """
    result = hashlib.sha1()
    for x in args:
        result.update(x.encode("utf-8"))
    return result.hexdigest()


def create_digest(slots):
    """
    Returns a naive consistent hashing function over 'slots'
    """
    def _digest(*args):
        item = _simple_digest(*args)
        x = [(_simple_digest(n, item), n) for n in slots ]
        return os.path.join(min(x)[1], item)
    return _digest


def get_subs(path):
    """
    Returns all subfolders in the given path
    """
    subs = [x for x in os.listdir(path)
            if os.path.isdir(os.path.join(path, x))]
    return subs
