from django.contrib import admin
from .models import ShippingAddress, Billboards, HeaderBanner

# Register your models here.

admin.site.register(ShippingAddress)
admin.site.register(Billboards)
admin.site.register(HeaderBanner)