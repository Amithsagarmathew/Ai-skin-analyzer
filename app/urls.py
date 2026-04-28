from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('sign-in.html', views.sign_in, name='sign_in'),
    path('sign-up.html', views.sign_up, name='sign_up'),
    path('profile.html', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('analysis.html', views.analysis_view, name='analysis'),
    path('routines.html', views.routines_view, name='routines'),
    path('progress.html', views.progress_view, name='progress'),
    path('history/', views.scan_history, name='scan_history'),
    path('scan/<int:scan_id>/', views.scan_detail, name='scan_detail'),
    path('shop.html', views.shop_view, name='shop'),
    path('single-product.html', views.single_product_view, name='single_product'),
    path('logout', views.sign_out, name='logout'),
    
    # E-commerce Routes
    path('cart.html', views.view_cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-item/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/increase/<int:item_id>/', views.increase_cart_item, name='increase_cart_item'),
    path('cart/decrease/<int:item_id>/', views.decrease_cart_item, name='decrease_cart_item'),
    path('checkout.html', views.checkout_view, name='checkout'),
    path('order-success/<int:order_id>/', views.order_success_view, name='order_success'),
    
    # Admin Panel Routes
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/products/', views.admin_products_list, name='admin_products_list'),
    path('admin-panel/products/add/', views.admin_product_add, name='admin_product_add'),
    path('admin-panel/products/edit/<int:product_id>/', views.admin_product_edit, name='admin_product_edit'),
    path('admin-panel/products/delete/<int:product_id>/', views.admin_product_delete, name='admin_product_delete'),
    path('admin-panel/users/', views.admin_users_list, name='admin_users_list'),
    path('admin-panel/users/delete/<int:user_id>/', views.admin_user_delete, name='admin_user_delete'),
    
    # User Orders
    path('orders.html', views.user_orders, name='orders'),
]
