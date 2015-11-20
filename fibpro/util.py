import json
import base64
import six
import sys
from threading import local
from time import sleep
from binascii import Error as BinasciiError

_threadlocal = None

def get_threadlocal():
    global _threadlocal
    if not _threadlocal:
        _threadlocal = local()
    if not hasattr(_threadlocal, 'data'):
        setattr(_threadlocal, 'data', {})
    return getattr(_threadlocal, 'data')

def dict_set(dictionary, key_path, value):
    d = dictionary
    for key in key_path[:-1]:
        next_dict = d.get(key, {})
        d[key] = next_dict
        d= next_dict
    d[key_path[-1]] = value
    return dictionary

def dict_get(dictionary, key_path, default_value=None):
    for key in key_path[:-1]:
        if key not in dictionary:
            return default_value
        dictionary = dictionary[key]
    return dictionary.get(key_path[-1], default_value)

def dict_map_string(dictionary, map_fn):
    for key, value in dictionary.iteritems():
        if isinstance(value, six.string_types):
            dictionary[key] = map_fn(value)
        if type(value) == dict and value:
            dict_map_string(value, map_fn)
    return dictionary


def load_config(config_file=None):
    config = {}
    if config_file is None:
        return config
    if type(config_file) == list:
        file_list = config_file
    else:
        file_list = [config_file]
    for filename in file_list:
        with open(filename, "r") as f:
            config.update(json.loads(f.read()))
    return config

def get_server_port():
    for i in xrange(len(sys.argv)):
        if sys.argv[i] == "-b":
            return sys.argv[i+1].split(':')[1]
    return None

class RetryException(Exception):
    def __init__(self, exception, *args):
        self.exception = exception
        super(RetryException, self).__init__(*args)

def _retry_default_post_attempt(e):
    sleep(1)
    return False

def retry(
        try_function,
        retries=3,
        post_attempt=_retry_default_post_attempt,
        raise_last_exception=False):
    last_exception = None
    for i in xrange(0, retries):
        try:
            return try_function()
        except Exception, last_exception:
            give_up = post_attempt(last_exception)
            if give_up == True:
                break
    if raise_last_exception and last_exception is not None:
        raise last_exception
    raise RetryException(last_exception)

# Copied from django source: https://docs.djangoproject.com/en/1.8/_modules/django/utils/http/#urlsafe_base64_encode
def urlsafe_base64_encode(s):
    """
    Encodes a bytestring in base64 for use in URLs, stripping any trailing
    equal signs.
    """
    return base64.urlsafe_b64encode(s).rstrip(b'\n=')


def urlsafe_base64_decode(s):
    """
    Decodes a base64 encoded string, adding back any trailing equal signs that
    might have been stripped.
    """
    s = force_bytes(s)
    try:
        return base64.urlsafe_b64decode(s.ljust(len(s) + len(s) % 4, b'='))
    except (LookupError, BinasciiError) as e:
        raise ValueError(e)

# Copied from django source
def force_bytes(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_bytes, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if isinstance(s, bytes):
        if encoding == 'utf-8':
            return s
        else:
            return s.decode('utf-8', errors).encode(encoding, errors)
    if strings_only and (s is None or isinstance(s, int)):
        return s
    if isinstance(s, Promise):
        return six.text_type(s).encode(encoding, errors)
    if not isinstance(s, six.string_types):
        try:
            if six.PY3:
                return six.text_type(s).encode(encoding)
            else:
                return bytes(s)
        except UnicodeEncodeError:
            if isinstance(s, Exception):
                # An Exception subclass containing non-ASCII data that doesn't
                # know how to print itself properly. We shouldn't raise a
                # further exception.
                return b' '.join([force_bytes(arg, encoding, strings_only,
                        errors) for arg in s])
            return six.text_type(s).encode(encoding, errors)
    else:
        return s.encode(encoding, errors)
