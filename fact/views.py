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

from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
from django.contrib import messages

import django.contrib.auth
import django.contrib.auth.models
import fact.models
import fact.forms

def login(request):
    if request.method == 'POST':
        loginform = fact.forms.LoginForm(request.POST)
        if loginform.is_valid():
            user = django.contrib.auth.authenticate(username=loginform.cleaned_data['username'], password=loginform.cleaned_data['password'])
            if user is not None:
                if user.is_active:
                    django.contrib.auth.login(request, user)
                    return redirect(reverse('home'))
                else:
                    messages.add_message(request, messages.ERROR, _('Your account is not activated.'))
            else:
                messages.add_message(request, messages.ERROR, _('Wrong user name or password.'))
        else:
            messages.add_message(request, messages.ERROR, _('Please provide a user name and password.'))

    else:
        loginform = fact.forms.LoginForm()

    return render_to_response('fact/login.html', {
            'title' : _('Log in'),
            'loginform' : loginform
        }, context_instance=RequestContext(request))

def logout(request):
    django.contrib.auth.logout(request)
    return redirect(reverse('home'))

@login_required
def index(request):
    invoices = fact.models.Invoice.invoices().all()
    return render_to_response('fact/index.html', {
            'title' : _('Invoices'),
            'invoices' : invoices
        }, context_instance=RequestContext(request))

@login_required
def customers(request):
    customers = fact.models.Customer.objects.all().order_by('name')
    return render_to_response('fact/customers.html', {
            'title' : _('Customers'),
            'customers' : customers
        }, context_instance=RequestContext(request))

@login_required
def detailed(request, guid):
    invoice = get_object_or_404(fact.models.Invoice, pk=guid)
    return render_to_response('fact/detailed.html', {
            'title' : _('Invoice %s') % invoice.id,
            'invoice' : invoice,
            'customer' : invoice.customer,
            'job' : invoice.job
        }, context_instance=RequestContext(request))

@login_required
def pdf(request, guid):
    import settings
    import reportlab.pdfgen.canvas
    from reportlab.lib import pagesizes, units, colors, utils
    from reportlab.platypus import Paragraph, Image
    from reportlab.platypus.tables import Table, TableStyle
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from django.contrib.humanize.templatetags.humanize import intcomma

    company = fact.models.Slot.company()
    invoice = get_object_or_404(fact.models.Invoice, pk=guid)
    if not invoice.date_posted or not invoice.date_due:
        return redirect(reverse('fact.views.detailed', kwargs={'guid':guid}))

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=' + _('invoice') + '-' + invoice.id + '.pdf'
    p = reportlab.pdfgen.canvas.Canvas(response, pagesize=pagesizes.A4)
    width, height = pagesizes.A4
    font = 'Helvetica'

    # Right-hand stuff
    x = units.cm * 14;
    p.setFont(font + '-Bold', 18)
    p.drawString(x, height-(units.cm*4.5), _('Invoice %s') % invoice.id)
    p.setFont(font, 10)
    p.drawString(x, height-(units.cm*5.5), _('Invoice date: %s') % invoice.date_invoice.strftime('%d.%m.%Y'))
    p.drawString(x, height-(units.cm*6), _('Due date: %s') % invoice.date_due.strftime('%d.%m.%Y'))

    # Logo
    img = utils.ImageReader(settings.FACT_LOGO)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    img = Image(settings.FACT_LOGO, width=units.cm*4, height=units.cm*4*aspect)
    img.drawOn(p, x+(units.cm*1), height-(units.cm*2.25))

    # Left-hand header stuff
    x = units.cm * 2;
    p.setFont(font + '-Oblique', 8)
    p.drawString(x, height-(units.cm*1.25), company['name'])
    address = company['address'].split("\n")
    base = 1.65
    for a in address:
        p.drawString(x, height-(units.cm*base), a)
        base += 0.4


    # Recipient name and address
    y = units.cm*4.5
    base = 0.5
    customer = invoice.customer
    p.setFont(font, 10)
    p.drawString(x, height-y, customer.name); y += units.cm*base
    p.drawString(x, height-y, customer.addr_addr1); y += units.cm*base
    p.drawString(x, height-y, customer.addr_addr2); y += units.cm*base
    p.drawString(x, height-y, customer.addr_addr3); y += units.cm*base
    p.drawString(x, height-y, customer.addr_addr4); y += units.cm*base
    y += units.cm*2

    # Main
    p.setFont(font + '-Bold', 14)
    p.drawString(x, height-y, 'Specification')
    y += units.cm*1
    p.setFont(font, 10)
    fmt = '{0:.2f}'

    # Get our invoice entries, headers, etc
    style = TableStyle()
    invoice_entries = []
    headers = [_('Description'), _('Amount'), _('Type'), _('Unit price'), _('VAT'), _('Net')]
    style.add('FONT', (0,0), (-1,0), font + '-Bold')
    style.add('LINEBELOW', (0,0), (-1,0), 1, colors.black)
    for entry in invoice.entries:
        invoice_entries.append([
            entry.description,
            intcomma(fmt.format(entry.quantity)),
            _(entry.action),
            intcomma(fmt.format(entry.unitprice)),
            intcomma(fmt.format(entry.tax_percent)) + '%',
            intcomma(fmt.format(entry.net))
        ])
    style.add('LINEBELOW', (0, len(invoice_entries)), (-1, len(invoice_entries)), 1, colors.black)
    sums = []
    sums.append([_('Net'), '', '', '', '', intcomma(fmt.format(invoice.net))])
    sums.append([_('VAT'), '', '', '', '', intcomma(fmt.format(invoice.tax))])
    if invoice.payments.count() > 0:
        sums.append([_('Subtotal'), '', '', '', '', intcomma(fmt.format(invoice.gross))])
        style.add('LINEBELOW', (0, len(invoice_entries)+3), (-1, len(invoice_entries)+3), 1, colors.black)
        for payment in invoice.payments.all():
            sums.append([_('Paid %s') + payment.post_date.strftime('%d.%m.%Y'), '', '', '', '', intcomma(fmt.format(payment.amount))])
        ln = len(invoice_entries) + len(sums)
        style.add('LINEBELOW', (0, ln), (-1, ln), 1, colors.black)
    else:
        style.add('LINEBELOW', (0, len(invoice_entries)+2), (-1, len(invoice_entries)+2), 1, colors.black)
    sums.append([_('Amount due'), '', '', '', '', intcomma(fmt.format(invoice.due))])
    ln = len(invoice_entries) + len(sums)
    style.add('BACKGROUND', (0, ln), (-1, ln), colors.wheat)
    style.add('FONT', (0, ln), (-1, ln), font + '-Bold')
    style.add('LINEBELOW', (0, ln), (-1, ln), 2, colors.black)

    # Draw the table
    t = Table([headers] + invoice_entries + sums,
            ([units.cm*6.5, units.cm*1.75, units.cm*2, units.cm*2.5, units.cm*2, units.cm*2.25])
            )
    t.setStyle(style)
    w, h = t.wrapOn(p, units.cm*19, units.cm*8)
    y += h
    t.drawOn(p, x, height-y)
    y += units.cm*2.5

    # Bank account number
    stylesheet = getSampleStyleSheet()
    #pr = u'Beløpet betales til konto: ' + company['bank_account_number'] + '.'
    #p.drawString(x, y, pr)
    if invoice.notes:
        txt = invoice.notes + '<br/><br/>'
    else:
        txt = ''
    txt += _('Amount payable to bank account: <b>') + company['bank_account_number'] + '</b>.'
    pr = Paragraph(txt, stylesheet['BodyText'])
    w, h = pr.wrapOn(p, units.cm*19, units.cm*6)
    pr.drawOn(p, x, height-y)

    # Footer stuff
    p.setFont(font + '-BoldOblique', 8)
    p.drawString(x, units.cm*2.8, company['name'])
    p.setFont(font + '-Oblique', 8)
    p.drawString(x, units.cm*2.4, address[0])
    p.drawString(x, units.cm*2, address[1])

    p.drawString(units.cm*8, units.cm*2.4, 'Web: ' + company['url'])
    p.drawString(units.cm*8, units.cm*2, 'E-post: ' + company['email'])

    p.drawString(units.cm*14, units.cm*2.4, 'Telefon: ' + company['phone'])
    p.drawString(units.cm*14, units.cm*2, 'Org.nr: ' + company['id'])

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()

    return response
