# -*- encoding: utf-8 -*-

import re
from urlparse import urlparse,urlunparse

import lxml.html
from pyquery import PyQuery

class AddressParser(object):
    def __getattr__(self, attr):
        if re.match('[a-zA-Z_][a-zA-Z0-9_]*', attr) != None:
            try:
                value = self.match.group(attr).strip()
                if attr == 'street':
                    value = re.sub(r'([Ss])tr\.',u'\\1traße',value)
                    value = re.sub(r'([Pp])l\.',r'\1latz',value)
                if attr == 'number':
                    value = re.sub(r'\s+','',value)
                    value = value.lower()
                return value
            except IndexError:
                return None
            except AttributeError:
                return None
        else:
            raise ValueError('Attribute names must be valid identifiers.')
    
    def address_is_empty(self):
        return self.match == None
    
    def __init__(self, address_string):
        street_pattern = '(?P<street>[\s\WA-Za-z]+[0-9]*)'
        number_pattern = r'(?P<number>[0-9]+[A-Za-z]{0,1}((\s*-\s*)*[0-9]+[A-Za-z]{0,1}){0,1})'
        zip_pattern = r'(?P<zip_code>[0-9]{5})'
        city_pattern = r'(?P<city>[\s\w-]+)'
        district_pattern = r'\({0,1}\s*(?P<district>[^,()]*)\s*\){0,1}'
        self.match = re.search(
                r'(%s\s+%s,\s+){0,1}%s\s+%s(,\s*%s){0,1}' % 
                    (
                        street_pattern,
                        number_pattern,
                        zip_pattern,
                        city_pattern,
                        district_pattern,
                    ), 
                address_string
            )

class ExposeParser(object):
    abstract_methods = (
            '_is_not_online',
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
        )
    
    def __init__(self, expose_link):
        self._expose_link = expose_link
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
            elif attr == 'expose_not_online':
                return self._is_not_online()
            elif attr == 'address':
                return self._get_address()
            elif attr == 'district':
                return self._get_district()
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
    
    def _get_district(self,address):
        if address.district == None:
            pass # TODO
            return ''
        return address.district
    
    def _get_address(self, address_string = None):
        if address_string == None:
            address_string = self._get_address_string()
        address = AddressParser(address_string)
        if address.address_is_empty():
            return {}
        else:
            return {
                    'street': address.street if address.street != None else '',
                    'number': address.number if address.number != None else '',
                    'nation': address.nation if address.nation != None else '',
                    'state': address.state if address.state != None else '',
                    'zip_code': address.zip_code if address.zip_code != None else '',
                    'city': address.city if address.city != None else '',
                    'district': self._get_district(address),
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
    
    def _is_not_online(self):
        return self._get_title() == 'Objekt nicht gefunden'
    
    def _get_contact(self):
        realtor_box = self.pyquery("div#anbieter div.boxContPad").html()
        if realtor_box == None:
            return {}
        impressum_link = re.search('href="(?P<link>/immobilienmakler/impressum-[^"]*)"',realtor_box)
        contact = dict()
        if impressum_link != None:
            tostring = lambda node, method='text': \
                    lxml.html.tostring(node, method=method, encoding='iso-8859-1') \
                    if node != None else ''
            expose_url = urlparse(self._expose_link)
            impressum_link = urlunparse((
                    expose_url.scheme,
                    expose_url.netloc,
                    impressum_link.group('link'),
                    None,None,None
                ))
            pyquery = PyQuery(lxml.html.parse(impressum_link).getroot())
            name = pyquery('div.content h2')
            contact['name'] = tostring(name[0]).strip()
            paragraphs = pyquery('div.content p')
            if len(paragraphs) > 1:
                address = tostring(paragraphs[1],'html')
                address = re.sub(',*\s*<br\s*/{0,1}>',', ',address)
                address = re.sub('<.*>','',address)
                address = re.sub('\s+',' ',address)
                address = self._get_address(address.strip())
                contact.update(address)
            contact_table = pyquery('div.content table tr')
            for row in contact_table:
                if len(row) > 1:
                    if tostring(row[0]).lower().find('telefon') >= 0:
                        contact['phone'] = tostring(row[1])
                    if tostring(row[0]).lower().find('telefax') >= 0:
                        contact['fax'] = tostring(row[1])
                    if tostring(row[0]).lower().find('mobil') >= 0:
                        contact['mobile'] = tostring(row[1])
                    if tostring(row[0]).lower().find('e-mail') >= 0:
                        contact['mail'] = tostring(row[1])
                    if tostring(row[0]).lower().find('homepage') >= 0:
                        contact['web'] = tostring(row[1])
        return contact
    
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
    def _is_not_online(self):
        return self._get_title() == 'Objekt nicht gefunden'
    
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
    
    def _get_contact(self):
        realtor_box = self.pyquery("div#is24-expose-realtor-box").html()
        if realtor_box == None:
            return {}
        impressum_link = re.search('href="(?P<link>[^"]*realtorId=[0-9]*)"',realtor_box)
        contact = dict()
        web = self.pyquery("a#is24-expose-realtor-box-homepage").text()
        contact['web'] = web.strip() if web else ''
        for span in self.pyquery("div.is24-phone p span"):
            if span.text.lower().find('telefon') == 0:
                contact['phone'] = span.tail.strip() if span.tail else ''
            elif span.text.lower().find('mobil') == 0:
                contact['mobile'] = span.tail.strip() if span.tail else ''
            elif span.text.lower().find('fax') == 0:
                contact['fax'] = span.tail.strip() if span.tail else ''
        if impressum_link != None:
            expose_url = urlparse(self._expose_link)
            impressum_link = urlunparse((
                    expose_url.scheme,
                    expose_url.netloc,
                    impressum_link.group('link'),
                    None,None,None
                ))
            pyquery = PyQuery(lxml.html.parse(impressum_link).getroot())
            name = pyquery('div#is24-content h3').text()
            contact['name'] = name.strip() if name != None else ''
            paragraphs = pyquery('div#is24-content p')
            address = paragraphs.html().strip()
            if address != None:
                address = address.replace('<br />',', ')
                address = re.sub('(&#13;)*','',address)
                address = re.sub('\s+',' ',address)
                address = self._get_address(address)
                contact.update(address)
            if len(paragraphs) > 1:
                for child in paragraphs[1]:
                    if child.tag == 'span':
                        if child.text.lower().find('tel') == 0 and \
                                contact.get('phone') == None:
                            contact['phone'] = child.tail.strip()
                        elif child.text.lower().find('fax') == 0 and \
                                contact.get('fax') == None:
                            contact['fax'] = child.tail.strip()
                        elif child.text.lower().find('e-mail') == 0 and \
                                contact.get('mail') == None:
                            contact['mail'] = child.tail.strip()
        return contact
    
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
        return self.pyquery("td.is24qa-heizungsart").text()
    
    def _get_object_state(self):
        return self.pyquery("td.is24qa-objektzustand").text()
    
    def _get_security(self):
        security = self.pyquery("td.is24qa-kaution-oder-genossenschaftsanteile")
        security('a.is24-internal').remove()
        security = security.text()
        if security == None:
            security = self.pyquery("td.is24-mortgage")
            security('a.is24-internal').remove()
            security = security.text()
        return security
        
    def _get_commission(self):
        return self.pyquery("td.is24qa-provision").text()
    
    def _get_space(self):
        return ImmoscoutExposeParser._get_float(
                self.pyquery("td.is24qa-wohnflaeche-ca").text()
            )
    
    def _get_floor(self):
        floor = self.pyquery("td.is24qa-etage").text()
        if floor == None:
            return floor
        return int(floor)
    
    def _get_flat_type(self):
        return self.pyquery("td.is24qa-wohnungstyp").text()
    
    def _get_rooms(self):
        return ImmoscoutExposeParser._get_float(
                self.pyquery("td.is24qa-zimmer").text()
            )
    
    def _get_year(self):
        year = self.pyquery("td.is24qa-baujahr").text()
        if year == None:
            return year
        return int(year)
    
    def _get_availability(self):
        return self.pyquery("td.is24qa-bezugsfrei-ab").text()

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
