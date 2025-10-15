from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('profile/', views.profile_edit, name='profile_edit'),
    path('products/', views.product_list, name='product_list'),
    # contact
    path('contact/', views.contact, name='contact'),

    # cart & checkout
    path('cart/', views.cart_detail, name='cart_detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/<int:order_id>/', views.payment_success, name='payment_success'),
    path('receipt/<int:order_id>/', views.receipt, name='receipt'),
    path('signup/', views.signup_view, name='signup'),
]
