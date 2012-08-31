from django.db import models
from django.db.models import Q
from dateutil.relativedelta import relativedelta

# Create your models here.

class Transaction(models.Model):

    guid = models.CharField(primary_key=True, max_length=32)
    post_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'transactions'


class Split(models.Model):

    guid = models.CharField(primary_key=True, max_length=32)
    tx_guid = models.CharField(max_length=32)
    lot_guid = models.CharField(max_length=32)
    value_num = models.IntegerField()
    value_denom = models.IntegerField()

    @property
    def amount(self):
        return 1.00 * self.value_num / self.value_denom

    @property
    def transaction(self):
        return Transaction.objects.get(pk=self.tx_guid)

    @property
    def post_date(self):
        return self.transaction.post_date

    class Meta:
        managed = False
        db_table = 'splits'


class Term(models.Model):

    guid = models.CharField(primary_key=True, max_length=32)
    duedays = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'billterms'


class TaxtableEntry(models.Model):

    taxtable = models.CharField(max_length=32)
    amount_num = models.IntegerField()
    amount_denom = models.IntegerField()

    @property
    def amount(self):
        return 1.00 * self.amount_num / self.amount_denom

    class Meta:
        managed = False
        db_table = 'taxtable_entries'


class Customer(models.Model):

    guid = models.CharField(primary_key=True, max_length=32)
    name = models.CharField(max_length=2048)
    addr_name = models.CharField(max_length=2048)
    addr_addr1 = models.CharField(max_length=2048)
    addr_addr2 = models.CharField(max_length=2048)
    addr_addr3 = models.CharField(max_length=2048)
    addr_addr4 = models.CharField(max_length=2048)

    class Meta:
        managed = False
        db_table = 'customers'


class Job(models.Model):

    guid = models.CharField(primary_key=True, max_length=32)
    name = models.CharField(max_length=2048)
    owner_guid = models.CharField(max_length=32)
    owner_type = models.IntegerField()

    @property
    def customer(self):
        if self.owner_type == 2:
            return Customer.objects.get(pk=self.owner_guid)
        elif self.owner_type == 3:
            return self.job.customer
        return None

    @property
    def job(self):
        if self.owner_type == 3:
            return Job.objects.get(pk=self.owner_guid)
        return None

    @property
    def address(self):
        return [self.addr_addr1, self.addr_addr2, self.addr_addr3, self.addr_addr4]

    class Meta:
        managed = False
        db_table = 'jobs'


class Entry(models.Model):

    guid = models.CharField(primary_key=True, max_length=32)
    invoice = models.CharField(max_length=32)
    description = models.CharField(max_length=2048)
    action = models.CharField(max_length=2048)
    quantity_num = models.IntegerField()
    quantity_denom = models.IntegerField()
    i_price_num = models.IntegerField()
    i_price_denom = models.IntegerField()
    i_discount_num = models.IntegerField()
    i_discount_denom = models.IntegerField()
    i_taxtable = models.CharField(max_length=32)
    i_taxable = models.IntegerField()
    i_taxincluded = models.IntegerField()

    @property
    def quantity(self):
        return 1.00 * self.quantity_num / self.quantity_denom

    @property
    def unitprice(self):
        return 1.00 * self.i_price_num / self.i_price_denom

    @property
    def net(self):
        return 1.00 * self.unitprice * self.quantity

    @property
    def tax_percent(self):
        return TaxtableEntry.objects.get(taxtable=self.i_taxtable).amount

    @property
    def tax(self):
        return self.net * self.tax_percent * 0.01

    @property
    def gross(self):
        return self.net + self.tax

    class Meta:
        managed = False
        db_table = 'entries'


class Invoice(models.Model):

    guid = models.CharField(primary_key=True, max_length=32)
    id = models.CharField(max_length=2048)
    terms = models.CharField(max_length=32)
    notes = models.CharField(max_length=2048)
    date_opened = models.DateTimeField()
    date_posted = models.DateTimeField()
    owner_guid = models.CharField(max_length=32)
    owner_type = models.IntegerField()
    post_lot = models.CharField(max_length=32)

    @staticmethod
    def invoices():
        return Invoice.objects.filter(Q(owner_type=3) | Q(owner_type=2)).order_by('-id')

    @property
    def transactions(self):
        return Split.objects.filter(guid=self.guid)
    
    @property
    def entries(self):
        return Entry.objects.filter(invoice=self.guid)

    @property
    def paid(self):
        return sum([x.amount for x in self.payments])

    @property
    def due(self):
        return sum([x.amount for x in self.transactions])

    @property
    def net(self):
        return sum([x.net for x in self.entries])

    @property
    def tax(self):
        return sum([x.tax for x in self.entries])

    @property
    def gross(self):
        return sum([x.gross for x in self.entries])

    @property
    def customer(self):
        if self.owner_type == 2:
            return Customer.objects.get(pk=self.owner_guid)
        elif self.owner_type == 3:
            return self.job.customer
        return None

    @property
    def job(self):
        if self.owner_type == 3:
            return Job.objects.get(pk=self.owner_guid)
        return None

    @property
    def date_due(self):
        days = Term.objects.get(pk=self.terms).duedays
        return self.date_posted + relativedelta(days=+days)

    @property
    def transactions(self):
        if self.post_lot is None:
            return Split.objects.none()
        return Split.objects.filter(lot_guid=self.post_lot)

    @property
    def payments(self):
        return self.transactions.filter(value_num__lte=0)

    @property
    def paid(self):
        if self.date_posted is not None and self.due == 0:
            return True
        return False
    
    class Meta:
        managed = False
        db_table = 'invoices'
