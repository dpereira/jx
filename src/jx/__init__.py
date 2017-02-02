"""
jx - Json eXplorer

"""

import curses
import json
import threading
import time

from processors import init_processors, process

version = '0.1'

class JsonLoader:

    def __init__(self, file_path):
        with open(file_path, 'r') as f: 
            self.json = f.read()
            self.data = json.loads(self.json)

class JsonParser:

    object_index = {}

    def _buffer_add(self, instance, text, line=0, level=0, i=0, inline=False, label=['root'], exc=False):
        buffer = ',' if i  else ''
        buffer += '' if inline else '\n' + ('\t' * level)
        buffer += text
        l = line + (0 if inline and not exc else 1)
        self.object_index[l] = instance, label
        return buffer, l

    def _expand_ctx(self, ctx):
        return (
            ctx.get('line', 0),
            ctx.get('level', 0),
            ctx.get('attribute_index', 0),
            ctx.get('label', ['root'])
        )

    def _new_ctx(self, line, level, attribute_index, label):
        return {
            'line': line,
            'level': level,
            'attribute_index': attribute_index, 
            'label': label
        }

    def print_object(self, instance, ctx={}):
        line, level, attribute_index, label = self._expand_ctx(ctx)
        buffer = ''
        b,line = self._buffer_add(instance, "{", line, inline=True, i=attribute_index, label=label)
        buffer +=  b

        for i, (attr, value) in enumerate(instance.items()):
            b, line = self._buffer_add(instance, '{k}: '.format(k=json.dumps(attr)), line, level + 1, i, label=label)
            buffer += b
            if isinstance(value, dict):
                child_ctx = self._new_ctx(
                    line, level + 1, i, label + [attr]
                )
                o, line = self.print_object(value, child_ctx)
                    
            elif isinstance(value, list):
                # TODO: support lists
                child_ctx = self._new_ctx(
                    line, level + 1, i, label + [attr]
                )
                o, line = self.print_object({}, child_ctx)
            else:
                o = json.dumps(value)

            b, line = self._buffer_add(instance, o, line, level + 1, i=0, inline=True, label=label)
            buffer += b

        b, line = self._buffer_add(instance, "}", line, level, 0, inline=(len(instance)==0), exc=True, label=label)
        buffer += b

        return buffer, line


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
