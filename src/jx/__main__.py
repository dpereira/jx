"""
jx - Json eXplorer

Usage:
    jx <json-file-path>
"""


from docopt import docopt
from jx import Jx


arguments = docopt(__doc__, version=Jx.version)

jx = Jx(*(arguments.get(k, None) for k in []))
with jx:
    jx.run(arguments['<json-file-path>'])

#for i, l in enumerate(jx.buffer[0].split('\n')):
#   try:
#       print('{:>10}> {}'.format(jx.index[i][-1],l))
#   except KeyError as e:
#       print('FAILED for {} ({})'.format(l ,e))
