import random
from .forms import ReviewForm
from django.urls import reverse
from django.contrib import messages
from accounts.models import Cart, CartItem
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from products.models import Product, SizeVariant, ColorVariant, ProductReview, Wishlist
from home.models import HeaderBanner, OpenAIConfiguration
from openai import OpenAI, AuthenticationError, APIConnectionError, OpenAIError

# Create your views here.

def get_product(request, slug):
    banners= HeaderBanner.objects.all()
    product = get_object_or_404(Product, slug=slug)
    sorted_size_variants = product.size_variant.all().order_by('size_name')
    related_products = list(product.category.products.filter(parent=None).exclude(uid=product.uid))
    openai_config = OpenAIConfiguration.objects.filter().first()

    # Review product view
    review = None
    if request.user.is_authenticated:
        try:
            review = ProductReview.objects.filter(product=product, user=request.user).first()
        except Exception as e:
            print("No reviews found for this product", str(e))
            messages.warning(request, "No reviews found for this product")

    rating_percentage = 0
    if product.reviews.exists():
        rating_percentage = (product.get_rating() / 5) * 100

    if request.method == 'POST' and request.user.is_authenticated:
        if review:
            # If review exists, update it
            review_form = ReviewForm(request.POST, instance=review)
        else:
            # Otherwise, create a new review
            review_form = ReviewForm(request.POST)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            messages.success(request, "Review added successfully!")
            return redirect('get_product', slug=slug)
    else:
        review_form = ReviewForm()

    # Related product view
    if len(related_products) >= 4:
        related_products = random.sample(related_products, 4)

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    context = {
        "banners": banners,
        'product': product,
        'sorted_size_variants': sorted_size_variants,
        'related_products': related_products,
        'review_form': review_form,
        'rating_percentage': rating_percentage,
        'in_wishlist': in_wishlist,
        'openai_config': openai_config
    }

    if request.GET.get('size', 'color'):
        size = request.GET.get('size')
        color = request.GET.get('color')
        quantity = request.GET.get('quantity')
        price = product.get_product_price(size, color, quantity)

        print(f"\n\nsize: {size}, color: {color}, and quantity: {quantity}\n\n")

        from urllib.parse import quote

        context['selected_size'] = quote(size or '')
        context['selected_color'] = quote(color or '')
        context['selected_quantity'] = quote(quantity or '')
        context['updated_price'] = price

    return render(request, 'product/product.html', context=context)


# Product Review view
@login_required
def product_reviews(request):
    banners= HeaderBanner.objects.all()
    reviews = ProductReview.objects.filter(
        user=request.user).select_related('product').order_by('-date_added')
    return render(request, 'product/all_product_reviews.html', {'reviews': reviews, "banners": banners,})


# Edit Review view
@login_required
def edit_review(request, review_uid):
    review = ProductReview.objects.filter(uid=review_uid, user=request.user).first()
    if not review:
        return JsonResponse({"detail": "Review not found"}, status=404)
    
    if request.method == "POST":
        stars = request.POST.get("stars")
        content = request.POST.get("content")
        review.stars = stars
        review.content = content
        review.save()
        messages.success(request, "Your review has been updated successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return JsonResponse({"detail": "Invalid request"}, status=400)

# Like and Dislike review view
def like_review(request, review_uid):
    review = ProductReview.objects.filter(uid=review_uid).first()

    if request.user in review.likes.all():
        review.likes.remove(request.user)
    else:
        review.likes.add(request.user)
        review.dislikes.remove(request.user)
    return JsonResponse({'likes': review.like_count(), 'dislikes': review.dislike_count()})


def dislike_review(request, review_uid):
    review = ProductReview.objects.filter(uid=review_uid).first()

    if request.user in review.dislikes.all():
        review.dislikes.remove(request.user)
    else:
        review.dislikes.add(request.user)
        review.likes.remove(request.user)
    return JsonResponse({'likes': review.like_count(), 'dislikes': review.dislike_count()})


# delete review view
def delete_review(request, slug, review_uid):
    if not request.user.is_authenticated:
        messages.warning(request, "You need to be logged in to delete a review.")
        return redirect('login')

    review = ProductReview.objects.filter(uid=review_uid, product__slug=slug, user=request.user).first()
    
    if not review:
        messages.error(request, "Review not found.")
        return redirect('get_product', slug=slug)

    review.delete()
    messages.success(request, "Your review has been deleted.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Like and Dislike review view
def generate_description(request, product_uid):
    try:
        # Get the product
        product = Product.objects.get(uid=product_uid)
    except Product.DoesNotExist:
        return JsonResponse({"error": "Product not found"}, status=404)

    # Get OpenAI config
    openai_config = OpenAIConfiguration.objects.filter(is_active=True).first()
    if not openai_config:
        # return JsonResponse({"error": "OpenAI configuration is missing"}, status=500)
        return JsonResponse({"error": "Something went wrong on our end."}, status=500)

    client = OpenAI(api_key=openai_config.api_key)

    try:
        # Call OpenAI API
        response = client.chat.completions.create(
            model=openai_config.model,
            messages=[
                {"role": "system", "content": openai_config.instructions},
                {"role": "user", "content": f"Product name: {product.brand} {product.product_name}"}
            ]
        )
        product_description = response.choices[0].message.content.strip()

        # Save description to database
        product.product_description = product_description
        product.save()

        return JsonResponse({'description': product_description})

    except AuthenticationError:
        # return JsonResponse({"error": "OpenAI authentication failed. Check your API key."}, status=401)
        return JsonResponse({"error": "Something went wrong on our end."}, status=401)
    except APIConnectionError:
        # return JsonResponse({"error": "Failed to connect to OpenAI. Try again later."}, status=503)
        return JsonResponse({"error": "Something went wrong on our end."}, status=503)
    except OpenAIError as e:
        # Catch other OpenAI-related errors
        # return JsonResponse({"error": f"OpenAI API error: {str(e)}"}, status=500)
        return JsonResponse({"error": "Something went wrong on our end."}, status=500)
    except Exception as e:
        # Catch any other unexpected errors
        # return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)
        return JsonResponse({"error": "Something went wrong on our end."}, status=500)


# Add a product to Wishlist
@login_required
def add_to_wishlist(request, uid):
    size_variant = request.GET.get('size')
    color_variant = request.GET.get('color')
    quantity = request.GET.get('quantity')

    print(f"\n\nSize Variant: {size_variant}, Color Variant: {color_variant}, Quantity: {quantity}\n\n")
    if size_variant in [None, "", "None"] or color_variant in [None, "", "None"]:
        messages.warning(request, 'Please select size, color, and quantity before adding to the wishlist!')
        return redirect(request.META.get('HTTP_REFERER', '/'))

    product = get_object_or_404(Product, uid=uid)
    size_variant = get_object_or_404(SizeVariant, size_name=size_variant)
    color_variant = get_object_or_404(ColorVariant, color_name=color_variant)

    wishlist, created = Wishlist.objects.get_or_create(
        user=request.user, 
        product=product, 
        size_variant=size_variant, 
        color_variant=color_variant
        )
    
    if not created:
        wishlist.quantity += int(quantity) if quantity and int(quantity) >= 0 else 1
        wishlist.save()
        messages.success(request, "Product quantity updated in Wishlist!")

    if created:
        wishlist.quantity=quantity if quantity and int(quantity) >= 0 else 1
        wishlist.save()
        messages.success(request, "Product added to Wishlist!")

    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)


# Remove product from wishlist
@login_required
def remove_from_wishlist(request, uid):
    product = get_object_or_404(Product, uid=uid)
    size_variant_name = request.GET.get('size')

    if size_variant_name:
        size_variant = get_object_or_404(SizeVariant, size_name=size_variant_name)
        Wishlist.objects.filter(
            user=request.user, product=product, size_variant=size_variant).delete()
    else:
        Wishlist.objects.filter(user=request.user, product=product).delete()

    messages.success(request, "Product removed from wishlist!")
    return redirect(reverse('wishlist'))


# Wishlist View
@login_required
def wishlist_view(request):
    banners= HeaderBanner.objects.all()
    wishlist_items = Wishlist.objects.filter(user=request.user)
    return render(request, 'product/wishlist.html', {'wishlist_items': wishlist_items, "banners": banners,})


# Move to cart functionality on wishlist page.
def move_to_cart(request, uid):
    product = get_object_or_404(Product, uid=uid)
    wishlist = Wishlist.objects.filter(user=request.user, product=product).first()

    if not wishlist:
        messages.error(request, "Item not found in wishlist.")
        return redirect('wishlist')

    size_variant = wishlist.size_variant
    color_variant = wishlist.color_variant
    quantity = wishlist.quantity
    wishlist.delete()

    cart, created = Cart.objects.get_or_create(user=request.user, is_paid=False)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        size_variant=size_variant,
        color_variant=color_variant
        )

    if not created:
        cart_item.quantity += int(quantity) if quantity and int(quantity) >= 0 else 1
        cart_item.save()
        messages.success(request, 'Item quantity updated in cart successfully.')

    if created:
        cart_item.quantity=quantity if quantity and int(quantity) >= 0 else 1
        cart_item.save()
        messages.success(request, "Product moved to cart successfully!")

    referer = request.META.get('HTTP_REFERER', '/')
    return redirect(referer)
