import threading
import time
import requests
from .models import Cart, CartItem, Order, OrderItem
from django.shortcuts import get_object_or_404
from django.http import Http404
from urllib.parse import parse_qsl

# Create an order view
def create_order(cart, status):
    order, created = Order.objects.get_or_create(
        user=cart.user,
        paynow_reference=cart.paynow_reference,
        payment_status=status,
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

def poll_payment_status(paynow_reference):
    """
    Polls Paynow’s poll_url until the payment_status changes from pending,
    then updates your Order.payment_status and order creation if needed.
    """
    # Indicate polling has begun in background
    print(f"[Polling] Background polling started for reference: {paynow_reference}")

    try:
        cart = get_object_or_404(Cart, paynow_reference=paynow_reference)
    except Http404:
        print(f"[Polling] No order found for reference: {paynow_reference}")
        return

    # You saved the poll_url in Order.shipping_address or another field?
    poll_url = cart.paynow_poll_url  # ← replace with actual poll_url field!

    for attempt in range(6):  # retry for up to 3 minutes (6 × 30s)
        print(f"[Polling] Attempt {attempt + 1}/6 for {paynow_reference}")
        time.sleep(30)

        try:
            response = requests.get(poll_url, timeout=10)
            raw = response.text  # e.g. "reference=...&paynowreference=...&amount=...&status=..."
            data = dict(parse_qsl(raw))

            status = data.get('status')
            # poll_url = data.get('pollurl')
            # reference = data.get('reference')
            # paynow_ref = data.get('paynowreference')
            # amount = data.get('amount')
            # hash_val = data.get('hash')

            print(f"[Polling] Status: {status}")
            if status == 'Paid' or status == 'Awaiting Delivery':
                cart.is_paid = True
                cart.save()

                # Create the order after payment is confirmed
                create_order(cart, status)
                print(f"[Polling] Payment confirmed for {paynow_reference}")
                break

        except Exception as e:
            print(f"[Polling] Error polling {paynow_reference}: {e}")

def start_polling_task(paynow_reference):
    """
    Starts a daemon thread to poll payment status in the background.
    """
    print(f"[Polling] Starting background thread for {paynow_reference}")
    t = threading.Thread(target=poll_payment_status, args=(paynow_reference,))
    t.daemon = True
    t.start()
