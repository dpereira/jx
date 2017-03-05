"""
jx - Json eXplorer

"""

import curses
import json
import threading
import time

from parsers import JsonParser
from processors import init_processors, process

version = '0.1'

class JsonLoader:

    def __init__(self, file_path):
        with open(file_path, 'r') as f: 
            self.json = f.read()
            self.data = json.loads(self.json)

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

        for i, l in enumerate(self.buffer.split('\n')):
            #object_rep = json.dumps(self.index[i][1], sort_keys=True)
            #object_name = self.index[i][-1][-1]

            self._window.addstr('\r{}'.format(l))
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
