"""
transformers - text and data manipulation

"""

class Folder:

    _folded = {}

    def setup(self, window, jx):
        self._window = window
        self._jx = jx

    def seek(self, locator):
        parent = obj = self._jx.data
        for k in locator:
            parent = obj
            obj = obj[k]

        return parent, obj

    def transform(self, locator):
        target_name = locator[-1]
        fold_key = ''.join(locator)

        folded = self._folded.pop(fold_key, None)

        if folded:
            parent, obj = folded
            if parent:
                parent[target_name] = obj
            else:
                self._jx.data = obj
        else:
            if len(locator) > 1:
                parent, obj = self.seek(locator[1:])
                parent[target_name] = {}
            else:
                obj = self._jx.data 
                parent = None
                self._jx.data = {}
            self._folded[fold_key] = parent, obj
