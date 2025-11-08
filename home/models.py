from django.contrib.auth.models import User
from base.models import BaseModel
from django.urls import reverse
from django.db import models
from django import forms
from django_countries.fields import CountryField
from django.utils.html import mark_safe
from encrypted_model_fields.fields import EncryptedCharField

# avdertisement models
class Billboards(BaseModel):
    billboard_name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='billboards')

    def img_preview(self):
        return mark_safe(f'<img src="{self.image.url}" width="500"/>')
    
    def __str__(self) -> str:
        return self.billboard_name
    
class HeaderBanner(BaseModel):
    name = models.CharField(max_length=100)
    content = models.CharField(max_length=100)

    def __str__(self) -> str:
        return self.name   

# shipping address model
class ShippingAddress(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    street = models.CharField(max_length=100)
    street_number = models.CharField(max_length=10)
    zip_code = models.CharField(max_length=30)
    city = models.CharField(max_length=50)
    country = CountryField()
    phone = models.CharField(max_length=30)
    current_address = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.street}, {self.street_number}, {self.city}, {self.country}, {self.zip_code}, {self.phone}'

    def get_absolute_url(self):
        return reverse('shipping-address')

class ShippingAddressForm(forms.ModelForm):
    save_address = forms.BooleanField(required=False, label='Save the billing addres')

    class Meta:
        model = ShippingAddress
        fields = [
            'first_name',
            'last_name',
            'street',
            'street_number',
            'zip_code',
            'city',
            'country',
            'phone'
        ]

            
class OpenAIApikeyBucket(models.Model):
    api_key_name= models.CharField(max_length=100)
    api_key = EncryptedCharField(max_length=200)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)