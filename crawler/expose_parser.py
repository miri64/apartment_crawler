import re

class ExposeParser():
    def __getattr__(self, attr):
        if re.match('[a-zA-Z_][a-zA-Z0-9_]*')
            return eval('_get_%s()' % attr)
        else:
            raise ValueError('Attribute names must be valid identifiers.')
    
    def __init__():
        self.pyquery = PyQuery(lxml.html.parse(expose_link).getroot())

