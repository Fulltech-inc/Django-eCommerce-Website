from django.db.models import Q
from django.shortcuts import render
from products.models import Product, Category, ProductBrand
from home.models import HeaderBanner, Billboards
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

# Create your views here.


def index(request):
    query = Product.objects.all()
    categories = Category.objects.all()

    brands = ProductBrand.objects.all()
    banners= HeaderBanner.objects.all()
    billboards= Billboards.objects.all()

    selected_sort = request.GET.get('sort')
    selected_category = request.GET.get('category')

    if selected_category:
        query = query.filter(category__category_name=selected_category)

    if selected_sort:
        if selected_sort == 'newest':
            query = query.filter(newest_product=True).order_by('category_id')
        elif selected_sort == 'priceAsc':
            query = query.order_by('price')
        elif selected_sort == 'priceDesc':
            query = query.order_by('-price')

    page = request.GET.get('page', 1)
    paginator = Paginator(query, 20)

    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
    except Exception as e:
        print(e)

    context = {
        'brands': brands,
        'banners': banners,
        'billboards': billboards,
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'selected_sort': selected_sort,
    }
    return render(request, 'home/index.html', context)


def product_search(request):
    banners= HeaderBanner.objects.all()
    query = request.GET.get('q', '')

    if query:
        # Search for products that contain the query string in their product_name field
        products = Product.objects.filter(Q(product_name__icontains=query) | Q(
            product_name__istartswith=query))
    else:
        products = Product.objects.none()

    context = {'query': query, 'products': products, "banners": banners}
    return render(request, 'home/search.html', context)


def contact(request):
    banners= HeaderBanner.objects.all()
    context = {"form_id": "xgvvlrvn", "banners": banners}
    return render(request, 'home/contact.html', context)


def about(request):
    banners= HeaderBanner.objects.all()
    context = {"banners": banners}
    return render(request, 'home/about.html', context)


def terms_and_conditions(request):
    banners= HeaderBanner.objects.all()
    context = {"banners": banners}
    return render(request, 'home/terms_and_conditions.html', context)


def privacy_policy(request):
    banners= HeaderBanner.objects.all()
    context = {"banners": banners}
    return render(request, 'home/privacy_policy.html', context)
