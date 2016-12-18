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

    def print_object(self, instance, line=0, level=0, previous_i=0, label=['root']):
        buffer = ''
        b,line = self._buffer_add(instance, "{", line, inline=True, i=previous_i, label=label)
        buffer +=  b

        i = 0

        for i, (attr, value) in enumerate(instance.items()):
            b, line = self._buffer_add(instance, '{k}: '.format(k=json.dumps(attr)), line, level + 1, i, label=label)
            buffer += b
            if isinstance(value, dict):
                o, line = self.print_object(value, line, level + 1, label=label + [attr])
            elif isinstance(value, list):
                o, line = self.print_object({}, line, level + 1, label=label + [attr])
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
        self._window.keypad(True)
        curses.mousemask(curses.ALL_MOUSE_EVENTS)
        curses.noecho()
        init_processors(window=self._window, jx=self)

        return self

    def __exit__(self, *exception_args):
        curses.endwin()
        self._window = None

    def _print_data(self):
        jp = JsonParser()
        self.buffer = jp.print_object(self.data)
        self.index = jp.object_index
        for i, l in enumerate(self.buffer[0].split('\n')):
                self._window.addstr('\r{:>15}> {}\n'.format(self.index[i][-1][-1],l))

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
