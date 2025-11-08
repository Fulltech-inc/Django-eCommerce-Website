from django.contrib import admin
from .models import ShippingAddress, Billboards, HeaderBanner, OpenAIConfiguration

# Register your models here.

admin.site.register(ShippingAddress)
admin.site.register(Billboards)
admin.site.register(HeaderBanner)
admin.site.register(OpenAIConfiguration)