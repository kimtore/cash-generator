# -*- coding: utf-8 -*-
#
# Copyright (c) 2012, Kim Tore Jensen. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1) Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# 2) Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django.db import models
from django.db.models import Q
from dateutil import tz
from dateutil.relativedelta import relativedelta


class Option(models.Model):

    key = models.CharField(max_length=255)
    lang = models.CharField(max_length=5)
    value = models.TextField(null=True)

    @staticmethod
    def _get(key, lang):
        qs = Option.objects.filter(key=key, lang=lang)
        if qs.count() == 0:
            return None
        return qs[0]

    @staticmethod
    def get(key, lang):
        ob = Option._get(key, lang)
        if ob is None:
            return ob
        return ob.value

    @staticmethod
    def set(key, lang, value):
        ob = Option._get(key, lang)
        if ob is None:
            ob = Option(key=key, lang=lang)
        ob.value = value
        ob.save()

    @staticmethod
    def opt_list(lang):
        values = Option.objects.filter(lang=lang).values_list('key', 'value')
        initial = {}
        for key, value in values:
            initial[key] = value
        return initial

    class Meta:
        unique_together = ('key', 'lang')




##############################
######  GNUCASH MODELS  ######
##############################


class Slot(models.Model):

    name = models.CharField(max_length=4096)
    string_val = models.CharField(max_length=4096)

    @staticmethod
    def company():
        return {
                'id' : Slot.objects.get(name='options/Business/Company ID').string_val,
                # Due to lack of this option in the GnuCash GUI, we need
                # to hi-jack something else - Fax number is not very important.
                'bank_account_number' : Slot.objects.get(name='options/Business/Company Fax Number').string_val,
                'name' : Slot.objects.get(name='options/Business/Company Name').string_val,
                'address' : Slot.objects.get(name='options/Business/Company Address').string_val,
                'email' : Slot.objects.get(name='options/Business/Company Email Address').string_val,
                'url' : Slot.objects.get(name='options/Business/Company Website URL').string_val,
                'phone' : Slot.objects.get(name='options/Business/Company Phone Number').string_val,
            }

    class Meta:
        managed = False
        db_table = 'slots'


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
    action = models.CharField(max_length=2048)
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

    def __unicode__(self):
        return str(self.post_date) + ': ' + self.action + ' ' + str(self.amount)

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

    @property
    def invoices(self):
        jobs = [x.guid for x in self.jobs]
        jobs.append(self.guid)
        return Invoice.objects.filter(owner_guid__in=jobs)

    @property
    def jobs(self):
        return Job.objects.filter(owner_guid=self.guid)

    def __unicode__(self):
        return self.name

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
        if not self.i_taxable:
            return 0
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
    def date_invoice(self):
        date = self.date_posted.replace(tzinfo=tz.gettz('UTC'))
        return date.astimezone(tz.tzlocal())

    @property
    def date_due(self):
        days = Term.objects.get(pk=self.terms).duedays
        return self.date_invoice + relativedelta(days=+days)

    @property
    def transactions(self):
        if self.post_lot is None:
            return Split.objects.none()
        return Split.objects.filter(action='Invoice', lot_guid=self.post_lot)

    @property
    def all_transactions(self):
        if self.post_lot is None:
            return Split.objects.none()
        return Split.objects.filter(~Q(action='Auto Split'), lot_guid=self.post_lot)

    @property
    def payments(self):
        return self.transactions.filter(value_num__lte=0)

    @property
    def paid(self):
        if self.date_posted is not None and self.due == 0:
            return sum(self.transactions) == 0
        return False

    def __unicode__(self):
        return 'Invoice ' + self.id
    
    class Meta:
        managed = False
        db_table = 'invoices'
