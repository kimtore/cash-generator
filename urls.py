from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

# Add the urlpatterns for any custom Django applications here.
# You can also change the ``home`` view to add your own functionality
# to the project's homepage.

urlpatterns = patterns("",
    ("^admin/", include(admin.site.urls)),
    url("^$", 'fact.views.index', name='home'),
    ("^admin/?$", 'fact.views.admin'),
    ("^customers/?$", 'fact.views.customers'),
    ("^login/$", 'fact.views.login'),
    ("^logout/$", 'fact.views.logout'),
    ("^invoice/?$", 'fact.views.index'),
    ("^invoice/(?P<guid>\w{32})/?$", 'fact.views.detailed'),
    ("^invoice/pdf/(?P<guid>\w{32})/?$", 'fact.views.pdf'),
)
