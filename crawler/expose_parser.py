import re
import lxml.html

from pyquery import PyQuery

class AddressParser:
    def __getattr__(self, attr):
        if re.match('[a-zA-Z_][a-zA-Z0-9_]*', attr) != None:
            try:
                return self.match.group(attr)
            except IndexError:
                return None
            except AttributeError:
                return None
        else:
            raise ValueError('Attribute names must be valid identifiers.')
    
    def __init__(self, address_string):
        self.match = re.search(
                '((((?P<name>[\w\W]+), ){0,1}(?P<street>[\w\W]+)\W+(?P<number>[0-9]+[A-Za-z]*), ){0,1}(?P<zip_code>[0-9]{5}) (?P<city>[\w\W]+)){0,1}', 
                address_string, 
                re.UNICODE | re.LOCALE
            )

class ExposeParser:
    def __init__(self, expose_link):
        self.pyquery = PyQuery(lxml.html.parse(expose_link).getroot())
    
    def _get_title(self):
        return self.pyquery('title').text()
    
    def __getattr__(self, attr):
        if re.match('[a-zA-Z_][a-zA-Z0-9_]*', attr) != None:
            return eval('self._get_%s()' % attr)
        else:
            raise ValueError('Attribute names must be valid identifiers.')

class ImmonetExposeParser(ExposeParser):
    pass    # dummy

class ImmoscoutExposeParser(ExposeParser):
    pass    # dummy

class ImmoweltExposeParser(ExposeParser):
    pass    # dummy

class ExposeParserFactory():
    # __new__ and __init__ make this class a singleton
    # Source: http://de.wikipedia.org/wiki/Singleton_(Entwurfsmuster)#Implementierung_in_Python_.28ab_Version_2.2.29
    def __new__(type, *args):
        if not '_the_instance' in type.__dict__:
            type._the_instance = object.__new__(type)
        return type_the_instance
    
    def __init__(self):
        if not '_ready' in dir(self):
            self._ready = True
    
    def get_expose_parser(self, expose_link):
        if expose_link != None:
            if expose_link.find('immobilienscout24.de') >= 0:
                return ImmoscoutExposeParser(expose_link)
            elif expose_link.find('immonet.de') >= 0:
                return ImmonetExposeParser(expose_link)
            elif expose_link.find('immowelt.de') >= 0:
                return ImmoweltExposeParser(expose_link)
        raise Exception("Illegal Link: "+expose_link)
