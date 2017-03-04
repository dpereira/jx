"""
jx - Json eXplorer

"""

import curses
import json
import threading
import time

from collections import namedtuple
from processors import init_processors, process

version = '0.1'

class JsonLoader:

    def __init__(self, file_path):
        with open(file_path, 'r') as f: 
            self.json = f.read()
            self.data = json.loads(self.json)

class ParseException(Exception):
    pass


class TokenParser:

    token_names = [
        'OBJECT',
        'OBJ_OPEN',
        'OBJ_CLOSE',
        'LIST',
        'LIST_OPEN',
        'LIST_CLOSE',
        'KEY',
        'VALUE',
        'KEY_AND_VALUE',
        'KEY_AND_VALUE_SEPARATOR',
        'ROOT'
    ]

    tokens = namedtuple('Tokens', token_names)._make(token_names)

    def get_parser(self, token):
        return {
            self.tokens.OBJECT: JsonParser(),
            self.tokens.OBJ_OPEN: ConstantFragment('{'),
            self.tokens.OBJ_CLOSE: ConstantFragment('}'),
            self.tokens.LIST: DefaultParser(),
            self.tokens.LIST_OPEN: ConstantFragment('['),
            self.tokens.LIST_CLOSE: ConstantFragment(']'),
            self.tokens.KEY_AND_VALUE: KeyAndValueParser(),
            self.tokens.KEY_AND_VALUE_SEPARATOR: ConstantFragment(': '),
            self.tokens.KEY: DefaultParser(),
            self.tokens.VALUE: DefaultParser(),
        }[token]

    def _expand_ctx(self, ctx):
        return (
            ctx.get('line', 0),
            ctx.get('level', 0),
            ctx.get('attribute_index', 0),
            ctx.get('label', ['root']),
            ctx.get('inline', False)
        )

    def _new_ctx(self, line=0, level=0, attribute_index=0, label=['root'], inline=False, object_index={}):
        return {
            'line': line,
            'level': level,
            'attribute_index': attribute_index, 
            'label': label,
            'inline': inline,
            'object_index': object_index
        }


    def emit(self, instance, ctx, token):
        try:
            parser = self.get_parser(token)
        except KeyError as k:
            raise ParseException('{p} is not a valid token'.format(p=k))

        try:
            child_ctx = dict(ctx)
            fragment = parser.parse(instance, child_ctx)
            return fragment, child_ctx
        except Exception as e:
            raise
            #raise ParseException('Error parsing {t}: {te}, {e}'.format(t=token, te=type(e), e=e))

    def parse(self, instance, ctx):
        return (
            self.parse_before(instance, ctx) +
            self.parse_token(instance, ctx) +
            self.parse_after(instance, ctx)
        )

    def parse_token(self, instance, ctx):
        raise NotImplementedError('"parse" method implementation is required')

    def parse_before(self, instance, ctx):
        line, level, attribute_index, label, inline = self._expand_ctx(ctx)
        fragment = ',' if attribute_index  else ''
        fragment += '' if inline else '\n' + ('\t' * level)
        return fragment

    def parse_after(self, instance, ctx):
        ctx['line'] = self.line_number(instance, ctx)
        ctx['object_index'][ctx['line']] = instance, ctx['label']
        return ''

    def line_number(self, instance, ctx):
        return ctx['line'] + 1

class DefaultParser(TokenParser):

    def parse_token(self, key, ctx):
        return json.dumps(key)

class ConstantFragment(TokenParser):

    def __init__(self, fragment):
        self._fragment = fragment

    def parse_before(self, instance, ctx):
        return ''

    def line_number(self, instance, ctx):
        return ctx['line']

    def parse_token(self, instance, ctx):
        return self._fragment

class KeyAndValueParser(TokenParser):

    def parse_token(self, instance, ctx):
        key, value = instance
        key_fragment, ctx = self.emit(key, ctx, self.tokens.KEY)
        key_value_separator_fragment, ctx = self.emit(instance, ctx, self.tokens.KEY_AND_VALUE_SEPARATOR)

        if isinstance(value, dict):
            token = self.tokens.OBJECT
        elif isinstance(value, list):
            token = self.tokens.LIST
        else:
            token = self.tokens.VALUE

        value_fragment, ctx = self.emit(value, ctx, token)

        return '"{k}"{s} "{v}" '.format(
            k=key_fragment,
            s=key_value_separator_fragment,
            v=value_fragment
        )

class JsonParser(TokenParser):

    object_index = {}

    def _buffer_add(self, instance, text, line=0, level=0, i=0, inline=False, label=['root'], exc=False):
        buffer = text
        return buffer, l

    def parse_before(self, instance, ctx):
        return '' 

    def parse_token(self, instance, ctx):
        fragment, ctx = self.emit(instance, ctx, self.tokens.OBJ_OPEN)

        for attribute_index, key_and_value in enumerate(instance.items()):
            ctx['attribute_index'] = attribute_index
            key_and_value_fragment, ctx = self.emit(key_and_value, ctx, self.tokens.KEY_AND_VALUE)
            fragment += key_and_value_fragment

        closure_fragment, ctx = self.emit(instance, ctx, self.tokens.OBJ_CLOSE)

        return fragment + closure_fragment

    def print_object(self, instance, ctx=None):
        return self.parse_token(instance, ctx if ctx else self._new_ctx(object_index=self.object_index))
#        line, level, attribute_index, label, inline = self._expand_ctx(ctx)
#        buffer = ''
#        b,line = self._buffer_add(instance, "{", line, inline=True, i=attribute_index, label=label)
#        buffer +=  b
#
#        for i, (attr, value) in enumerate(instance.items()):
#            b, line = self._buffer_add(instance, , line, level + 1, i, label=label)
#            buffer += '{k}: '.format(k=json.dumps(attr))
#            if isinstance(value, dict):
#                child_ctx = self._new_ctx(
#                    line, level + 1, i, label + [attr]
#                )
#                o, line = self.print_object(value, child_ctx)
#            elif isinstance(value, list):
#                # TODO: support lists
#                child_ctx = self._new_ctx(
#                    line, level + 1, i, label + [attr]
#                )
#                o, line = self.print_object({}, child_ctx)
#            else:
#                o = json.dumps(value)
#
#            b, line = self._buffer_add(instance, o, line, level + 1, i=0, inline=True, label=label)
#            buffer += b
#
#        b, line = self._buffer_add(instance, "}", line, level, 0, inline=(len(instance)==0), exc=True, label=label)
#        buffer += b
#
#        return buffer, line


class Jx:

    version = version


    def __init__(self, indent=4):
        self._indent = indent

    def __enter__(self):
        self._window = curses.initscr()
        self._init_colors()
        self._window.keypad(True)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.noecho()
        init_processors(window=self._window, jx=self)

        return self

    def _init_colors(self):
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_GREEN)

    def __exit__(self, *exception_args):
        curses.endwin()
        self._window = None

    def _print_data(self):
        jp = JsonParser()
        self.buffer = jp.print_object(self.data)
        self.index = jp.object_index
        seen_objects = set()

        for i, l in enumerate(self.buffer[0].split('\n')):
            object_rep = json.dumps(self.index[i][1], sort_keys=True)
            object_name = self.index[i][-1][-1]

            self._window.addstr('\r{:>15}> {}'.format(object_name, l))
            if object_rep not in seen_objects:
                seen_objects.add(object_rep)
                self._window.addstr(' ')
                self._window.addstr('-', curses.color_pair(1))

            self._window.addstr('\n')

    def _trap_events(self):
        curses.cbreak()
        
        try:
            key = self._window.getch()
            self._print_data()
            while key is not None:
                extra = None

                if key == curses.KEY_MOUSE:
                    extra = curses.getmouse()

                self._process_event(key, extra)

                self._window.move(0, 0)
                key = self._window.getch()

        except (KeyboardInterrupt, SystemExit):
            return
        except Exception as e:
            print('ERROR: {}'.format(e))
            raise

    def _process_event(self, key, extra):
        try:
            process(key, extra)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception  as e:
            self._window.addstr('\r{e}'.format(e=e))

    def run(self, file_path=None):
        if file_path:
            self.data = JsonLoader(file_path).data
        self._trap_events()
