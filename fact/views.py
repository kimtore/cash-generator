# -*- coding: utf-8 -*-

from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
import django.contrib.auth.models
import fact.models

@login_required
def index(request):
    invoices = fact.models.Invoice.invoices().all()
    return render_to_response('fact/index.html', {
            'title' : 'Fakturabehandling',
            'invoices' : invoices
        }, context_instance=RequestContext(request))

@login_required
def detailed(request, guid):
    invoice = fact.models.Invoice.objects.get(pk=guid)
    return render_to_response('fact/detailed.html', {
            'title' : 'Faktura ' + invoice.id,
            'invoice' : invoice,
            'customer' : invoice.customer,
            'job' : invoice.job
        }, context_instance=RequestContext(request))
