from django.db import models

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
