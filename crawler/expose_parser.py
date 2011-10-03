import re
import lxml.html

from pyquery import PyQuery

class AddressParser(object):
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

class ExposeParser(object):
    def __init__(self, expose_link):
        self.pyquery = PyQuery(lxml.html.parse(expose_link).getroot())
    
    def _get_title(self):
        return self.pyquery('title').text()
    
    @staticmethod
    def _get_float(o):
        f = re.search(
                '([0-9]+.)*[0-9]+(,[0-9]+){0,1}', 
                str(o), 
                re.UNICODE | re.LOCALE
            )
        if f != None:
            f = f.group()
            f = f.replace('.','')
            f = f.replace(',','.')
            return float(f)
        return 0.0
    
    def __getattr__(self, attr):
        if re.match('[a-zA-Z_][a-zA-Z0-9_]*', attr) != None:
            return eval('self._get_%s()' % attr)
        else:
            raise ValueError('Attribute names must be valid identifiers.')

class ImmonetExposeParser(ExposeParser):
    def _find_in_table(self,sub):
        try:
            return [n for n in self.pyquery("td.label") \
                    if unicode(n.text).find(sub) != -1
                ][0].getparent()[1]
        except IndexError:
            return None
    
    def _evaluate_table_value(self,key):
        value = self._find_in_table(key)
        tostring = lambda tag: lxml.html.tostring(tag, encoding='utf8', method='text')
        if value != None:
            if len(tostring(value).strip()) > 0:
                return tostring(value).strip()
        return None
    
    def _get_cold_rent(self):
        return ImmonetExposeParser._get_float(self._evaluate_table_value('Miete zzgl. NK'))

class ImmoscoutExposeParser(ExposeParser):
    pass    # dummy

class ImmoweltExposeParser(ExposeParser):
    def __init__(self,*args,**kwargs):
        super(ImmoweltExposeParser, self).__init__(*args,**kwargs)
        self._basic_values = dict()
        
        keys = self.pyquery('span.eckdatenbezeichner')
        values = self.pyquery('span.eckdatencontent')
        for l,v in zip(keys,values):
            key = lxml.html.tostring(l,encoding=unicode,method='text').strip().strip(':')
            value = lxml.html.tostring(v,encoding=unicode,method='text').strip()
            self._basic_values[key] = value
    
    def _get_cold_rent(self):
        return ImmoweltExposeParser._get_float(self._basic_values[u'Kaltmiete'])

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
