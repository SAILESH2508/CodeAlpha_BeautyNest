from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

import razorpay

from .models import Product, Category, Review, Profile, ContactMessage, Order, OrderItem
from .forms import ReviewForm, ProfileForm, ProductFilterForm, ContactForm, CustomSignUpForm
from .cart import Cart


# ---------------- Home & Product Views ---------------- #
def home(request):
    categories = Category.objects.all()
    form = ProductFilterForm(request.GET or None, categories=categories)
    products = Product.objects.all().select_related("category")

    q = request.GET.get("q")
    cat = request.GET.get("category")

    if q:
        products = products.filter(
            Q(name__icontains=q)
            | Q(description__icontains=q)
            | Q(skin_type_tags__icontains=q)
        )
    if cat:
        products = products.filter(category_id=cat)

    context = {
        "products": products.order_by("-created_at")[:24],
        "categories": categories,
        "form": form,
    }
    return render(request, "shop/home.html", context)


def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    q = request.GET.get("q")
    category = request.GET.get("category")

    if q:
        products = products.filter(name__icontains=q)
    if category:
        products = products.filter(category_id=category)

    return render(request, "shop/product_list.html", {
        "products": products,
        "categories": categories,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = product.reviews.all()
    form = ReviewForm()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        form = ReviewForm(request.POST)
        if form.is_valid():
            rev = form.save(commit=False)
            rev.product = product
            rev.user = request.user
            rev.save()
            messages.success(request, "✅ Review added successfully!")
            return redirect("product_detail", slug=slug)

    return render(request, "shop/product_detail.html", {
        "product": product,
        "reviews": reviews,
        "form": form,
    })


# ---------------- Profile ---------------- #
@login_required
def profile_edit(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Profile updated successfully.")
            return redirect("profile_edit")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "shop/profile_edit.html", {"form": form})


# ---------------- Contact ---------------- #
def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, "shop/contact.html", {
                "form": ContactForm(),
                "success": True,
            })
    else:
        form = ContactForm()
    return render(request, "shop/contact.html", {"form": form})


# ---------------- Cart ---------------- #
@login_required
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.add(product)
    messages.success(request, f"🛒 Added {product.name} to your cart!")
    return redirect("cart_detail")


@login_required
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    messages.info(request, f"❌ Removed {product.name} from your cart.")
    return redirect("cart_detail")


@login_required
def cart_detail(request):
    cart = Cart(request)
    return render(request, "shop/cart.html", {"cart": cart})


# ---------------- Checkout with Razorpay ---------------- #
@login_required
def checkout(request):
    cart = Cart(request)
    total = cart.get_total_price()

    if total <= 0:
        messages.error(request, "Your cart is empty!")
        return redirect("cart_detail")

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create order in Razorpay
    razorpay_order = client.order.create({
        "amount": int(round(total * 100)),  # amount in paise
        "currency": "INR",
        "payment_capture": 1,
    })

    # Create local order
    order = Order.objects.create(
        user=request.user,
        total=total,
        paid=False,
        razorpay_order_id=razorpay_order["id"]
    )

    context = {
        "cart": cart,
        "razorpay_order_id": razorpay_order["id"],
        "razorpay_key_id": settings.RAZORPAY_KEY_ID,
        "amount": int(round(total * 100)),
        "order": order,
    }
    return render(request, "shop/checkout.html", context)


# ---------------- Payment Callback ---------------- #
@csrf_exempt
def payment_success(request, order_id):  # ✅ Accept order_id from URL
    if request.method == "POST":
        razorpay_payment_id = request.POST.get("razorpay_payment_id")
        razorpay_order_id = request.POST.get("razorpay_order_id")
        razorpay_signature = request.POST.get("razorpay_signature")

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }

        try:
            # ✅ Verify Razorpay payment signature
            client.utility.verify_payment_signature(params_dict)

            # ✅ Mark order as paid
            order = Order.objects.get(id=order_id)
            order.paid = True
            order.razorpay_order_id = razorpay_order_id
            order.save()

            # ✅ Create OrderItems if not already created
            if not order.items.exists():
                cart = Cart(request)
                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        product=item["product"],
                        quantity=item["quantity"],
                        price=item["price"],
                    )
                cart.clear()

            messages.success(request, "🎉 Payment Successful! Thank you for your order.")
            return render(request, "shop/payment_success.html", {"order": order})

        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "❌ Payment verification failed. Please try again.")
            return redirect("checkout")

        except Order.DoesNotExist:
            messages.error(request, "⚠️ Invalid order. Please contact support.")
            return redirect("checkout")

    # Handle GET request (after redirect)
    try:
        order = Order.objects.get(id=order_id)
        return render(request, "shop/payment_success.html", {"order": order})
    except Order.DoesNotExist:
        messages.error(request, "⚠️ Invalid order ID.")
        return redirect("checkout")


# ---------------- Receipt ---------------- #
@login_required
def receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "shop/receipt.html", {"order": order})


# ---------------- Signup ---------------- #
def signup_view(request):
    if request.method == "POST":
        form = CustomSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data.get("password1")
            auth_user = authenticate(username=user.username, password=raw_password)
            if auth_user:
                login(request, auth_user)
                messages.success(request, "🎉 Account created & logged in successfully!")
                return redirect("product_list")
            else:
                messages.warning(request, "✅ Account created, but auto-login failed. Please log in manually.")
                return redirect("login")
        else:
            messages.error(request, "❌ Please correct the errors below and try again.")
    else:
        form = CustomSignUpForm()

    return render(request, "registration/signup.html", {"form": form})
