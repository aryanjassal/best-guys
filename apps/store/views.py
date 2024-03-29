from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.db.models import Q

from .models import *

def filter_products(request, filter):
    if filter == 'all':
        products = Product.objects.all()
        filter_type = 'all'
        filter = None
    else:
        products = Product.objects.filter(categories__slug=filter)
        filter_type = 'category'
        filter = Category.objects.get(slug=filter)

    return render(request, 'store/filter_products.html', {
        'products': products,
        'filter_type': filter_type,
        'filter': filter
    })

def search_products(request):
    if request.method == 'GET':
        q = request.GET.get('q')
        products = Product.objects.filter(Q(categories__name=q) | Q(name__icontains=q) | Q(long_name__icontains=q) | Q(slug__icontains=q) | Q(model__icontains=q))

        return render(request, 'store/filter_products.html', {
            'products': products,
            'filter_type': 'search',
            'search_val': q
        })

def product_details(request, slug):
    product = Product.objects.get(slug=slug)
    discount_percent = round(((product.price - product.sale_price) / product.price) * 100, 2)
    stars = [i.star_rating for i in Review.objects.filter(product=product)]

    try:
        average_rating = round(sum(stars) / len(stars))
    except:
        average_rating = 5

    paginator = Paginator(Review.objects.filter(product=product).order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    paginated_reviews = paginator.get_page(page_number)

    return render(request, 'store/product_layout.html', {
        'product': product,
        'discount_percent': discount_percent if discount_percent > 99 else round(discount_percent),
        'paginated_reviews': paginated_reviews,
        'all_reviews': Review.objects.filter(product=product),
        'average_rating': average_rating,
        'allow_reviews': (AllowReviews.objects.get(pk=1).allow or request.user.is_superuser or request.user.is_staff),
    })

def new_review(request, slug):
    if request.method == 'POST':
        new_review = Review(
            user=request.user if request.user.is_authenticated else None,
            product=Product.objects.get(slug=slug),
            title=request.POST.get('title'),
            body=request.POST.get('review'),
            recommended=True if request.POST.get('recommended') else False,
            star_rating=5 if request.POST.get('star-rating') == '' else int(request.POST.get('star-rating'))
        )
        new_review.save()

        return redirect('store:product_details', slug=slug)

def delete_review(request, slug, pk):
    review = Review.objects.get(product=Product.objects.get(slug=slug), pk=pk)
    review.delete()
    return redirect('store:product_details', slug=slug)
