import threading
import time
import requests
from .models import Cart, CartItem, Order, OrderItem
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import Http404

# Create an order view
def create_order(cart):
    order, created = Order.objects.get_or_create(
        user=cart.user,
        paynow_reference=cart.paynow_reference,
        payment_status="Paid",
        shipping_address=cart.user.profile.shipping_address,
        payment_mode="Paynow",
        order_total_price=cart.get_cart_total(),
        coupon=cart.coupon,
        grand_total=cart.get_cart_total_price_after_coupon(),
    )

    # Create OrderItem instances for each item in the cart
    cart_items = CartItem.objects.filter(cart=cart)
    for cart_item in cart_items:
        OrderItem.objects.get_or_create(
            order=order,
            product=cart_item.product,
            size_variant=cart_item.size_variant,
            color_variant=cart_item.color_variant,
            quantity=cart_item.quantity,
            product_price=cart_item.get_product_price()
        )

    return order

def poll_payment_status(paynow_reference):
    """
    Polls Paynow’s poll_url until the payment_status changes from pending,
    then updates your Order.payment_status and order creation if needed.
    """
    try:
        cart = get_object_or_404(Cart, paynow_reference=paynow_reference)
    except Http404:
        return

    # You saved the poll_url in Order.shipping_address or another field?
    poll_url = cart.paynow_poll_url  # ← replace with actual poll_url field!

    for _ in range(6):  # retry for up to 3 minutes (6 × 30s)
        time.sleep(30)

        try:
            resp = requests.get(poll_url, timeout=10)
            data = resp.json() if 'application/json' in resp.headers.get('Content-Type','') else resp.text

            # Simplest check: look for “paid” keyword
            if 'paid' in resp.text.lower():
                cart.is_paid = True
                cart.save()

                # Create the order after payment is confirmed
                order = create_order(cart)
                return

            # if 'failed' in resp.text.lower() or 'cancelled' in resp.text.lower():
            #     order.payment_status = 'Failed'
            #     order.save()
            #     return

        except Exception as e:
            print(f"[poll error for {paynow_reference}]:", e)

    # if still pending after retries
    # order.payment_status = 'Pending'
    # order.save()

def start_polling_task(paynow_reference):
    t = threading.Thread(target=poll_payment_status, args=(paynow_reference,))
    t.daemon = True
    t.start()
