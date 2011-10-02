from django.db import models
import expose_parser

class Address(models.Model):
    street = models.CharField(max_length=20)
    number = models.CharField(max_length=5)
    nation = models.CharField(max_length=3)
    state = models.CharField(max_length=30)
    zip_code = models.CharField(max_length=10)
    city = models.CharField(max_length=30)

class Contact(Address):
    name = models.CharField(max_length=30)
    phone = models.CharField(max_length=30)
    mobile = models.CharField(max_length=30)
    fax = models.CharField(max_length=30)
    web = models.CharField(max_length=100)
    mail = models.EmailField()

class Expose(models.Model):
    title = models.CharField(max_length=200)
    expose_link = models.CharField(max_length=100, primary_key=True)
    address = models.ForeignKey(Address, blank=True)
    contact = models.ForeignKey(Contact, related_name='offered_expose_set', blank=True)
    cold_rent = models.DecimalField(max_digits=6, decimal_places=2, blank=True)
    additional_charges = models.DecimalField(max_digits=6, decimal_places=2, blank=True)
    operation_expenses = models.DecimalField(max_digits=6, decimal_places=2, blank=True)
    heating_cost = models.DecimalField(max_digits=6, decimal_places=2, blank=True)
    total_rent = models.DecimalField(max_digits=6, decimal_places=2, blank=True)
    heating_type = models.CharField(max_length=20, blank=True)
    object_state = models.CharField(max_length=30, blank=True)
    security = models.DecimalField(max_digits=6, decimal_places=2, blank=True)
    commission = models.CharField(max_length=30, blank=True)
    space = models.DecimalField(max_digits=6, decimal_places=2, blank=True)
    floor = models.IntegerField(blank=True)
    flat_type = models.CharField(max_length=30, blank=True)
    rooms = models.DecimalField(max_digits=4, decimal_places=2, blank=True)
    year = models.IntegerField(blank=True)
    availability = models.CharField(max_length=30, blank=True)
    last_modified = models.DateField(auto_now=True, blank=True)
    
    def __init__(self,expose_link):
        parser = expose_parser.ExposeParserFactory().get_expose_parser(expose_link)
        super(Expose,self).__init__(
            title = parser.title,
            expose_link = expose_link,
        )
