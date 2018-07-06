"""
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
"""

import inspect
import pickle
import re
import sqlite3 as sqlite
import threading
from collections import MutableMapping
from contextlib import contextmanager
from functools import wraps


def typecasted(func):
    """Decorator that converts arguments via annotations."""
    signature = inspect.signature(func).parameters.items()

    @wraps(func)
    def wrapper(*args, **kwargs):
        args = list(args)
        new_args = []
        new_kwargs = {}
        for _, param in signature:
            converter = param.annotation
            if converter is inspect._empty:
                converter = lambda a: a  # do nothing
            if param.kind is param.POSITIONAL_OR_KEYWORD:
                if args:
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


def clansearch(k, v):
    valid = (
        'name', 'score', 'minMembers',
        'maxMembers', 'keys', 'exclude',
        'max', 'timeout'
    )
    k = _to_camel_case(k)
    if k not in valid:
        raise ValueError('Invalid search parameter passed: {}'.format(k))
    return k, v


def tournamentsearch(k, v):
    valid = (
        'name', 'keys', 'exclude',
        'max', 'timeout'
    )
    k = _to_camel_case(k)
    if k not in valid:
        raise ValueError('Invalid search parameter passed: {}'.format(k))
    return k, v


def keys(k, v):
    if k not in (
        'keys', 'exclude', 'max',
        'page', 'type', 'timeout'
    ):
        raise ValueError('Invalid url parameter passed: {}'.format(k))
    return k, ','.join(v) if isinstance(v, (list, tuple)) else v

def tournamentfilter(k, v):
    if k not in ('keys', 'exclude', 'max', 'page', 'type',
                 '1k', 'open', 'full', 'prep', 'joinable'):
        raise ValueError('Invalid url parameter passed: {}'.format(k))
    return k, ','.join(v) if isinstance(v, (list, tuple)) else v

def crtag(tag):
    tag = tag.strip('#').upper().replace('O', '0')
    allowed = '0289PYLQGRJCUV'
    bad = []
    for c in tag:
        if c not in allowed:
            bad.append(c)
    if bad or len(tag) < 3:
        raise ValueError("Invalid tag characters passed: {}".format(', '.join(bad)))
    return tag


first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def _to_snake_case(name):
    s1 = first_cap_re.sub(r'\1_\2', name)
    return all_cap_re.sub(r'\1_\2', s1).lower()


def _to_camel_case(snake):
    parts = snake.split('_')
    return parts[0] + "".join(x.title() for x in parts[1:])


class API:
    def __init__(self, url):
        self.BASE = url
        self.PLAYER = self.BASE + '/players'
        self.CLAN = self.BASE + '/clans'
        self.TOP = self.BASE + '/top'
        self.CONSTANTS = self.BASE + '/constants'
        self.POPULAR = self.BASE + '/popular'
        self.TOURNAMENT = self.BASE + '/tournaments'
        self.ENDPOINTS = self.BASE + '/endpoints'
        self.VERSION = self.BASE + '/version'
        self.AUTH = self.BASE + '/auth'


class SqliteDict(MutableMapping):
    def __init__(self, filename, table_name='data', fast_save=False, **options):
        self.filename = filename
        self.table_name = table_name
        self.fast_save = fast_save
        self.can_commit = True
        self._bulk_commit = False
        self._pending_connection = None
        self._lock = threading.RLock()
        with self.connection() as con:
            con.execute("create table if not exists `%s` (key PRIMARY KEY, value)" % self.table_name)

    @contextmanager
    def connection(self, commit_on_success=False):
        with self._lock:
            if self._bulk_commit:
                if self._pending_connection is None:
                    self._pending_connection = sqlite.connect(self.filename)
                con = self._pending_connection
            else:
                con = sqlite.connect(self.filename)
            try:
                if self.fast_save:
                    con.execute("PRAGMA synchronous = 0;")
                yield con
                if commit_on_success and self.can_commit:
                    con.commit()
            finally:
                if not self._bulk_commit:
                    con.close()

    def commit(self, force=False):
        if force or self.can_commit:
            if self._pending_connection is not None:
                self._pending_connection.commit()

    @contextmanager
    def bulk_commit(self):
        self._bulk_commit = True
        self.can_commit = False
        try:
            yield
            self.commit(True)
        finally:
            self._bulk_commit = False
            self.can_commit = True
            if self._pending_connection is not None:
                self._pending_connection.close()
                self._pending_connection = None

    def __getitem__(self, key):
        with self.connection() as con:
            row = con.execute("select value from `%s` where key=?" %
                              self.table_name, (key,)).fetchone()
            if not row:
                raise KeyError
            return pickle.loads(row[0])

    def __setitem__(self, key, item):
        with self.connection(True) as con:
            con.execute("insert or replace into `%s` (key,value) values (?,?)" %
                        self.table_name, (key, pickle.dumps(item)))

    def __delitem__(self, key):
        with self.connection(True) as con:
            cur = con.execute("delete from `%s` where key=?" %
                              self.table_name, (key,))
            if not cur.rowcount:
                raise KeyError

    def __iter__(self):
        with self.connection() as con:
            for row in con.execute("select key from `%s`" % self.table_name):
                yield row[0]

    def __len__(self):
        with self.connection() as con:
            return con.execute("select count(key) from `%s`" %
                               self.table_name).fetchone()[0]

    def clear(self):
        with self.connection(True) as con:
            con.execute("drop table `%s`" % self.table_name)
            con.execute("create table `%s` (key PRIMARY KEY, value)" %
                        self.table_name)

    def __str__(self):
        return str(dict(self.items()))
