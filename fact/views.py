# -*- coding: utf-8 -*-

from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.core.urlresolvers import reverse
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
    invoice = get_object_or_404(fact.models.Invoice, pk=guid)
    return render_to_response('fact/detailed.html', {
            'title' : 'Faktura ' + invoice.id,
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

    invoice = get_object_or_404(fact.models.Invoice, pk=guid)
    if not invoice.date_posted or not invoice.date_due:
        return redirect(reverse('fact.views.detailed', kwargs={'guid':guid}))

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=incendio-faktura-' + invoice.id + '.pdf'
    p = reportlab.pdfgen.canvas.Canvas(response, pagesize=pagesizes.A4)
    width, height = pagesizes.A4
    font = 'Helvetica'

    # Right-hand stuff
    x = units.cm * 14;
    p.setFont(font + '-Bold', 18)
    p.drawString(x, height-(units.cm*4.5), 'Faktura ' + invoice.id)
    p.setFont(font, 10)
    p.drawString(x, height-(units.cm*5.5), 'Fakturadato: ' + invoice.date_invoice.strftime('%d.%m.%Y'))
    p.drawString(x, height-(units.cm*6), 'Betalingsfrist: ' + invoice.date_due.strftime('%d.%m.%Y'))

    # Logo
    img = utils.ImageReader(settings.FACT_LOGO)
    iw, ih = img.getSize()
    aspect = ih / float(iw)
    img = Image(settings.FACT_LOGO, width=units.cm*4, height=units.cm*4*aspect)
    img.drawOn(p, x+(units.cm*1), height-(units.cm*2.25))

    # Left-hand header stuff
    x = units.cm * 2;
    p.setFont(font + '-Oblique', 8)
    company = fact.models.Slot.company()
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
    p.drawString(x, height-y, 'Fakturaspesifikasjon')
    y += units.cm*1
    p.setFont(font, 10)
    fmt = '{0:.2f}'

    # Get our invoice entries, headers, etc
    style = TableStyle()
    invoice_entries = []
    headers = ['Beskrivelse', 'Antall', 'Type', 'Stykkpris', 'MVA', 'Netto']
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
    sums.append(['Netto', '', '', '', '', intcomma(fmt.format(invoice.net))])
    sums.append(['MVA', '', '', '', '', intcomma(fmt.format(invoice.tax))])
    if invoice.payments.count() > 0:
        sums.append(['Subtotal', '', '', '', '', intcomma(fmt.format(invoice.gross))])
        style.add('LINEBELOW', (0, len(invoice_entries)+3), (-1, len(invoice_entries)+3), 1, colors.black)
        for payment in invoice.payments.all():
            sums.append(['Betalt ' + payment.post_date.strftime('%d.%m.%Y'), '', '', '', '', intcomma(fmt.format(payment.amount))])
        ln = len(invoice_entries) + len(sums)
        style.add('LINEBELOW', (0, ln), (-1, ln), 1, colors.black)
    else:
        style.add('LINEBELOW', (0, len(invoice_entries)+2), (-1, len(invoice_entries)+2), 1, colors.black)
    sums.append([u'Å betale', '', '', '', '', intcomma(fmt.format(invoice.due))])
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
    txt += u'Beløpet betales til konto: <b>' + company['bank_account_number'] + '</b>.'
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
