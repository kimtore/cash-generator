from django.conf.urls.defaults import patterns, include, url
from django.contrib import admin

from mezzanine.core.views import direct_to_template

admin.autodiscover()

# Add the urlpatterns for any custom Django applications here.
# You can also change the ``home`` view to add your own functionality
# to the project's homepage.

urlpatterns = patterns("",
    ("^admin/", include(admin.site.urls)),
    url("^$", 'fact.views.index', name='home'),
    ("^kunder/?$", 'fact.views.customers'),
    ("^login/$", 'fact.views.login'),
    ("^logout/$", 'fact.views.logout'),
    ("^invoice/?$", 'fact.views.index'),
    ("^invoice/(?P<guid>\w{32})/?$", 'fact.views.detailed'),
    ("^invoice/pdf/(?P<guid>\w{32})/?$", 'fact.views.pdf'),
    ("^", include("mezzanine.urls")),
)

# Adds ``STATIC_URL`` to the context of error pages, so that error
# pages can use JS, CSS and images.
handler500 = "mezzanine.core.views.server_error"
