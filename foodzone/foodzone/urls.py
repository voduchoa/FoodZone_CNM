# ============================================================================================================================================
from django.contrib import admin
from django.urls import path, include
from myapp import views 
from django.conf import settings 
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index,name="index"),
    path('contact/',views.contact_us,name="contact"),
    path('about/',views.about,name="about"),
    path('team/',views.team_members,name="team"),
    path('dishes/',views.all_dishes,name="all_dishes"),
    path('register/',views.register,name="register"),
    path('check_user_exists/',views.check_user_exists,name="check_user_exist"),
    path('login/', views.signin, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),
    path('dish/<int:id>/', views.single_dish, name='dish'),

    # Chatbot URLs
    path('chatbot/', views.chatbot, name='chatbot'),
    path('chatbot/query/', views.chatbot_query, name='chatbot_query'),

    # Chức năng người giao hàng
    path('register_shipper/', views.register_shipper, name='register_shipper'),
    path('shipper_dashboard/', views.shipper_dashboard, name='shipper_dashboard'),
    path('update_delivery_status/<int:delivery_id>/', views.update_delivery_status, name='update_delivery_status'),
    path('delivery_detail/<int:delivery_id>/', views.delivery_detail, name='delivery_detail'),
    path('update_location/', views.update_location, name='update_location'),
    
    # Chức năng nhà hàng
    path('register_restaurant/', views.register_restaurant, name='register_restaurant'),
    path('restaurant_dashboard/', views.restaurant_dashboard, name='restaurant_dashboard'),
    
    # Chức năng địa chỉ giao hàng
    path('manage_addresses/', views.manage_addresses, name='manage_addresses'),
    path('delete_address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('set_default_address/<int:address_id>/', views.set_default_address, name='set_default_address'),
    
    # Theo dõi đơn hàng
    path('track_order/<int:order_id>/', views.track_order, name='track_order'),

    path('paypal/',include('paypal.standard.ipn.urls')),
    path('payment_done/', views.payment_done, name='payment_done'),
    path('payment_cancel/', views.payment_cancel, name='payment_cancel'),
    
    # Payment URL
    
    path('', include('myapp.urls')),
]+static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)