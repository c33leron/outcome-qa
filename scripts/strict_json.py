"""Small shared JSON/terminal boundary. No network, execution or mutation."""
import json
import math
import re
import unicodedata
from pathlib import Path


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON object key')
        result[key] = value
    return result


def reject_constant(_value):
    raise ValueError('non-JSON numeric constant')


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        raise ValueError('nonfinite JSON number')
    return number


def loads(text):
    return json.loads(text, object_pairs_hook=unique_object,
                      parse_constant=reject_constant, parse_float=finite_float)


def load(path):
    return loads(Path(path).read_text(encoding='utf-8'))


# Fixed forbidden ranges shared byte-for-byte with published JSON schemas.
IDENTIFIER_PATTERN = '^(?=.*\\S)[^\x00-\x1f\x7f-\x9f\xad\u0600-\u0605\u061c\u06dd\u070f\u0890-\u0891\u08e2\u180e\u200b-\u200f\u2028-\u202e\u2060-\u2064\u2066-\u206f\ud800-\uf8ff\ufeff\ufff9-\ufffb\U000110bd\U000110cd\U00013430-\U0001343f\U0001bca0-\U0001bca3\U0001d173-\U0001d17a\U000e0001\U000e0020-\U000e007f\U000f0000-\U000ffffd\U00100000-\U0010fffd]+(?![\\s\\S])'

def identifier(value):
    return isinstance(value, str) and re.fullmatch(IDENTIFIER_PATTERN, value) is not None


def terminal(value):
    """Escape control/format characters, preserving ordinary human text."""
    return ''.join(json.dumps(c, ensure_ascii=True)[1:-1]
                   if unicodedata.category(c).startswith('C') or c in '\u2028\u2029' else c
                   for c in str(value))
