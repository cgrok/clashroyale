'''
MIT License

Copyright (c) 2017 kyb3r

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

import inspect
import re
from functools import wraps


def typecasted():
    '''Decorator that converts arguments via annotations.'''
    def deco(func):
        signature = inspect.signature(func).parameters.items()
        @wraps(func)
        def wrapper(*args, **kwargs):
            args = list(args)
            new_args = []
            new_kwargs = {}
            for name, param in signature:
                converter = param.annotation
                if converter is inspect._empty:
                    converter = lambda a: a # do nothing
                if param.kind is param.POSITIONAL_OR_KEYWORD:
                    to_conv = args.pop(0)
                    new_args.append(converter(to_conv))
                elif param.kind is param.VAR_POSITIONAL:
                    for a in args:
                        new_args.append(converter(a))
                else:
                    for k, v in kwargs.items():
                        nk, nv = converter(k, v)
                        new_kwargs[nk] = nv
            return func(*new_args, **new_kwargs)
        return wrapper
    return deco


def clansearch(k, v):
    valid = ('name', 'score', 'minMembers', 'maxMembers')
    k = _to_camel_case(k)
    if k not in valid:
        raise ValueError(f'Invalid search parameter passed: {param}')
    return k, v
    
def crtag(tag):
    tag = tag.strip('#').upper().replace('O', '0')
    allowed = '0289PYLQGRJCUV'
    bad = []
    for c in tag:
        if c not in allowed:
            bad.append(c)
    if bad:
        raise ValueError(f"Invalid tag characters passed: {', '.join(bad)}")
    return tag

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')

def _to_snake_case(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()

def _to_camel_case(snake):
    parts = snake.split('_')
    return parts[0] + "".join(x.title() for x in parts[1:])

class Endpoints:
    BASE = 'http://api.cr-api.com'
    PLAYER = BASE + '/players'
    CLAN = BASE + '/clans'
    SEARCH = CLAN + '/search'
    TOP = BASE + '/top'
    CONSTANTS = BASE + '/constants'
    POPULAR = BASE + '/popular'
