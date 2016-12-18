"""
Processors - handle events from jx event trap.

"""

import curses
import transformers

class NoProcessor(Exception):
    pass

class ProcessorError(Exception):
    pass

class Processor:

    def setup(self, window, jx):
        self._window = window
        self._jx = jx

    def process(self, key, extra):
        raise NotImplementedError("'process' method requires implementation")


class MouseEvent(Processor):
    """
    General processor for mouse events.

    Only delegates to more specialized processors.

    """

    def process(self, key, extra):
        mouse_command = extra[-1]
        process((key, mouse_command), extra)

class MouseRightClick(Processor):

    _folder = transformers.Folder()

    def setup(self, window, jx):
        super().setup(window, jx)
        self._folder.setup(window, jx)
    
    def process(self, key, extra):
        device, x, y, z, button = extra
        clicked = self._window.inch(y ,x )
        locator = self._jx.index[y][1]
        self._folder.transform(locator)
        self._window.clear()
        self._jx._print_data()
        self._window.addstr('\rclick @ line {x}, {y} w/ {t}'.format(x=x, y=y, t=locator))

class MouseDoubleRightClick(Processor):
    pass
    
_processors = {
    curses.KEY_MOUSE: MouseEvent(),
    (curses.KEY_MOUSE, curses.BUTTON1_CLICKED): MouseRightClick(),
    (curses.KEY_MOUSE, curses.BUTTON1_DOUBLE_CLICKED): MouseDoubleRightClick(),
}

def init_processors(**parameters):
    for p in _processors.values():
        p.setup(**parameters)

def process(key, extra, processors=_processors):
    try:
        processor = _processors[key]
    except KeyError as k:
        raise NoProcessor('No processor found for {k}'.format(k=k))

    try:
        processor.process(key, extra)
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        raise ProcessorError("{p} processor failed with <{e}>".format(
            p=processor, e=e))
