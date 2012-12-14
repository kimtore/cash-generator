cash-generator
==============

<code>Cash-generator</code> is a Django + Mezzanine web application that
generates pretty PDF invoices from your GnuCash invoices.


Requirements
------------

* Django >= 1.4
* Mezzanine >= 1.2.4
* Reportlab >= 2.6
* PIL >= 1.1.7
* A web server capable of running Django applications (e.g. nginx + uWSGI, or
  Apache2 + mod_wsgi)

    apt-get install python-pip python-dev python-imaging python-psycopg2
    pip install mezzanine


Quick installation
------------------

* Install dependencies
* Install the correct database adapter according to the format of your GnuCash
  database
* Copy <code>local_settings.py.template</code> to
  <code>local_settings.py</code> and fill out the blanks
* <code>./manage.py syncdb</code>
* Running <code>./manage.py runserver</code>
