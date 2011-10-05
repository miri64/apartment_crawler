import re
import lxml.html

from pyquery import PyQuery

class AddressParser(object):
    def __getattr__(self, attr):
        if re.match('[a-zA-Z_][a-zA-Z0-9_]*', attr) != None:
            try:
                return self.match.group(attr).strip()
            except IndexError:
                return None
            except AttributeError:
                return None
        else:
            raise ValueError('Attribute names must be valid identifiers.')
    
    def __init__(self, address_string):
        self.match = re.search(
                '((?P<street>[\s\w-]+)\s+(?P<number>[0-9]+[A-Za-z]*),\s+){0,1}(?P<zip_code>[0-9]{5})\s+(?P<city>[\s\w,-]+)\s*(\((?P<district>.*)\)){0,1}', 
                address_string, 
                re.UNICODE
            )

class ExposeParser(object):
    abstract_methods = (
            '_get_expose_link',
            '_get_address_string',
            '_get_contact',
            '_get_cold_rent',
            '_get_additional_charges',
            '_is_operation_expenses_in_additional_expenses',
            '_get_operation_expenses',
            '_is_heating_cost_in_additional_expenses',
            '_get_heating_cost',
            '_get_original_total_rent',
            '_get_heating_type',
            '_get_object_state',
            '_get_security',
            '_get_commission',
            '_get_space',
            '_get_floor',
            '_get_flat_type',
            '_get_rooms',
            '_get_year',
            '_get_availability',
            '_get_last_modified',
        )
    
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
        return None
    
    def __getattr__(self, attr):
        if re.match('[a-zA-Z_][a-zA-Z0-9_]*', attr) != None:
            if attr in ExposeParser.abstract_methods:
                if attr.find('_is_') == 0:
                    return lambda *args, **kwargs: False
                else:
                    return lambda *args, **kwargs: None
            if attr == 'title':
                return self._get_title()
            elif attr == 'address':
                return self._get_address()
            elif attr == 'contact':
                return self._get_contact()
            elif attr == 'cold_rent':
                return self._get_cold_rent()
            elif attr == 'additional_charges':
                return self._get_additional_charges()
            elif attr == 'operation_expenses':
                return self._get_operation_expenses()
            elif attr == 'oe_in_ac':
                return self._is_operation_expenses_in_additional_expenses()
            elif attr == 'heating_cost':
                return self._get_heating_cost()
            elif attr == 'hc_in_ac':
                return self._is_heating_cost_in_additional_expenses()
            elif attr == 'total_rent':
                return self._get_total_rent()
            elif attr == 'heating_type':
                return self._get_heating_type()
            elif attr == 'object_state':
                return self._get_object_state()
            elif attr == 'security':
                return self._get_security()
            elif attr == 'commission':
                return self._get_commission()
            elif attr == 'space':
                return self._get_space()
            elif attr == 'floor':
                return self._get_floor()
            elif attr == 'flat_type':
                return self._get_flat_type()
            elif attr == 'rooms':
                return self._get_rooms()
            elif attr == 'year':
                return self._get_year()
            elif attr == 'availability':
                return self._get_availability()
            elif attr == 'last_modified':
                return self._get_last_modified()
            else:
                return None
        else:
            raise ValueError('Attribute names must be valid identifiers.')
    
    def _get_total_rent(self):
        total_rent = 0.0
        for c in ('cold_rent','operation_expenses','heating_cost'):
            if     (c == 'heating_cost' and \
                    self._is_heating_cost_in_additional_expenses()) or \
                   (c == 'operation_expenses' and \
                    self._is_operation_expenses_in_additional_expenses()):
                continue
            cost = self.__getattr__(c)
            if cost != None:
                total_rent += cost
        original_total_rent = self._get_original_total_rent()
        if original_total_rent > total_rent:
            total_rent = original_total_rent
        return total_rent
    
    def _get_address(self):
        address = AddressParser(self._get_address_string())
        return {
                'street': address.street if address.street != None else '',
                'number': address.number if address.number != None else '',
                'nation': address.nation if address.nation != None else '',
                'state': address.state if address.state != None else '',
                'zip_code': address.zip_code if address.zip_code != None else '',
                'city': address.city if address.city != None else '',
            }

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
        return ImmonetExposeParser._get_float(
                self._evaluate_table_value('Miete zzgl. NK')
            )
    
    def _get_additional_charges(self):
        return ImmonetExposeParser._get_float(
                self._evaluate_table_value('Nebenkosten')
            )
    
    def _get_operation_expenses(self):
        return ImmoweltExposeParser._get_float(
                self._evaluate_table_value('Betriebskosten')
            )

class ImmoscoutExposeParser(ExposeParser):
    def _get_cold_rent(self):
        return ImmoscoutExposeParser._get_float(
                self.pyquery("strong.is24qa-kaltmiete").text()
            )
    
    def _get_address_string(self):
        address = lxml.html.tostring(self.pyquery("div.is24-ex-address p")[1],
                method="text",
                encoding="iso-8859-1"
            )
            
        if len(address) > 0:
            address = address.replace(',','')
            address = address.replace('\r','')
            address = address.replace('Karte ansehenStreet View','')
            address = address.strip()
            address = unicode(
                    re.sub('\n\s+', ', ', address),encoding='iso-8859-1'
                )
        
        return address
    
    def _get_additional_charges(self):
        return ImmoscoutExposeParser._get_float(
                self.pyquery("td.is24qa-nebenkosten").text()
            )
    
    def _is_heating_cost_in_additional_expenses(self):
        heating_cost = self.pyquery("td.is24qa-heizkosten").text()
            
        if heating_cost.find('in Nebenkosten') >= 0:
            return heating_cost.find('nicht in Nebenkosten') < 0
        return False
    
    def _get_heating_cost(self):
        return ImmoscoutExposeParser._get_float(
                self.pyquery("td.is24qa-heizkosten").text()
            )
    
    def _get_original_total_rent(self):
        return ImmoscoutExposeParser._get_float(
                self.pyquery("strong.is24qa-gesamtmiete").text()
            )
    
    def _get_heating_type(self):
        heating_type = self.pyquery("td.is24qa-heizungsart").text()
        return heating_type
    
    def _get_object_state(self):
        object_state = self.pyquery("td.is24qa-objektzustand").text()
        return object_state

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
        return ImmoweltExposeParser._get_float(
                self._basic_values.get(u'Kaltmiete')
            )
    
    def _get_additional_charges(self):
        return ImmoweltExposeParser._get_float(
                self._basic_values.get(u'Nebenkosten')
            )
    
    def _get_operation_expenses(self):
        return ImmoweltExposeParser._get_float(
                self._basic_values.get(u'Betriebskosten')
            )

class ExposeParserFactory():
    # __new__ and __init__ make this class a singleton
    # Source: http://de.wikipedia.org/wiki/Singleton_(Entwurfsmuster)#Implementierung_in_Python_.28ab_Version_2.2.29
    def __new__(type, *args):
        if not '_the_instance' in type.__dict__:
            type._the_instance = object.__new__(type)
        return type._the_instance
    
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
