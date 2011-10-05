from django.db import models, IntegrityError

from datetime import timedelta, date

import expose_parser

class Address(models.Model):
    street = models.CharField(max_length=20, default='')
    number = models.CharField(max_length=5, default='')
    nation = models.CharField(max_length=3, default='')
    state = models.CharField(max_length=30, default='')
    zip_code = models.CharField(max_length=10, default='')
    city = models.CharField(max_length=30, default='')
    
    class Meta:
        unique_together = (
                ('street','number','nation','state','zip_code','city',)
            )

class Contact(Address):
    name = models.CharField(max_length=30, default='')
    phone = models.CharField(max_length=30, default='')
    mobile = models.CharField(max_length=30, default='')
    fax = models.CharField(max_length=30, default='')
    web = models.CharField(max_length=100, default='')
    mail = models.EmailField(default='')

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
    address = models.ForeignKey(Address, blank=True, null=True)
    contact = models.ForeignKey(Contact, related_name='offered_expose_set', blank=True, null=True)
    cold_rent = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    additional_charges = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    operation_expenses = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    operation_expenses_in_additional_charges = models.BooleanField(default=False)
    heating_cost = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    heating_cost_in_additional_charges = models.BooleanField(default=False)
    total_rent = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    heating_type = models.CharField(max_length=50, blank=True, null=True)
    object_state = models.CharField(max_length=50, blank=True, null=True)
    security = models.CharField(max_length=50, blank=True, null=True)
    commission = models.CharField(max_length=50, blank=True, null=True)
    space = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    floor = models.IntegerField(blank=True, null=True)
    flat_type = models.CharField(max_length=50, blank=True, null=True)
    rooms = models.DecimalField(max_digits=3, decimal_places=1, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    availability = models.CharField(max_length=50, blank=True, null=True)
    last_modified = models.DateField(auto_now=True)
    
    @staticmethod
    def get_expose_by_link(expose_link):
        try:
            old_expose = Expose.objects.get(expose_link = expose_link)
            return old_expose
        except Expose.DoesNotExist:
            pass
        
        parser = expose_parser.ExposeParserFactory().get_expose_parser(expose_link)
        address = Address(**parser.address)
        try:
            address.save()
        except IntegrityError, e:
            if e.args[0] != 1062:
                raise e
            else:
                address = Address.objects.get(**parser.address)
        e = Expose(
                title = parser.title,
                expose_link = expose_link,
                address = address,
                cold_rent = parser.cold_rent,
                additional_charges = parser.additional_charges,
                operation_expenses = parser.operation_expenses,
                operation_expenses_in_additional_charges = parser.oe_in_ac,
                heating_cost = parser.heating_cost,
                heating_cost_in_additional_charges = parser.hc_in_ac,
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
            )
        e.save()
        return e
