from django.db import models

from datetime import timedelta, date

import expose_parser

class Address(models.Model):
    street = models.CharField(max_length=20)
    number = models.CharField(max_length=5)
    nation = models.CharField(max_length=3)
    state = models.CharField(max_length=30)
    zip_code = models.CharField(max_length=10)
    city = models.CharField(max_length=30)
    
    class Meta:
        unique_together = (
                ('street','number','nation','state','zip_code','city',)
            )

class Contact(Address):
    name = models.CharField(max_length=30)
    phone = models.CharField(max_length=30)
    mobile = models.CharField(max_length=30)
    fax = models.CharField(max_length=30)
    web = models.CharField(max_length=100)
    mail = models.EmailField()
    
    class Meta:
        unique_together = (
                (
                    'name','street','number','nation','state',
                    'zip_code','city','phone','mobile','fax','web',
                    'mail'
                )
            )

class ExposeManager(models.Manager):
    MAXIMUM_EXPOSE_AGE = timedelta(days=3)
    
    def get_query_set(self):
        query_set = super(ExposeManager, self).get_query_set()
        query_set.filter(
                last_modified__lte = date.today() - 
                        ExposeManager.MAXIMUM_EXPOSE_AGE
            ).delete()
        return query_set

class Expose(models.Model):
    objects = ExposeManager()
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
    
    @staticmethod
    def get_expose_by_link(expose_link):
        try:
            old_expose = Expose.objects.get(expose_link = expose_link)
            return old_expose
        except Expose.DoesNotExist:
            pass
        
        parser = expose_parser.ExposeParserFactory().get_expose_parser(expose_link)
        e = Expose(
                title = parser.title,
                expose_link = expose_link,
                cold_rent = parser.cold_rent,
                additional_charges = parser.additional_charges,
                operation_expenses = parser.operation_expenses,
                heating_cost = parser.heating_cost,
                total_rent = parser.total_rent,
                heating_type = parser.heating_type,
                object_state = parser.object_state,
                security = parser.security,
                commission = parser.commission,
                space = parser.space,
                floor = parser.floor,
                flat_type = parser.flat_type,
                rooms = parser.rooms,
                year = parser.year,
                availability = parser.availability,
                last_modified = parser.last_modified,
            )
        e.save()
        return e
