from django.contrib import admin
from .models import *

# Register your models here.


admin.site.register(Category)
admin.site.register(Coupon)

class ProductImageAdmin(admin.StackedInline):
    model = ProductImage

class ProductBrandAdmin(admin.StackedInline):
    model = ProductBrand

class ProductAdmin(admin.ModelAdmin):
    list_display = ['product_name', 'price']
    inlines = [ProductImageAdmin]


@admin.register(ColorVariant)
class ColorVariantAdmin(admin.ModelAdmin):
    list_display = ['color_name', 'price']
    model = ColorVariant


@admin.register(SizeVariant)
class SizeVariantAdmin(admin.ModelAdmin):
    list_display = ['size_name', 'price', 'order']

    model = SizeVariant

admin.site.register(Product, ProductAdmin)
admin.site.register(ProductImage)
admin.site.register(ProductBrand)
admin.site.register(ProductReview)

# ✅ Register Wishlist model
@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'size_variant', 'color_variant', 'added_on']
    search_fields = ['user__username', 'product__product_name']
    list_filter = ['added_on', 'size_variant', 'color_variant']