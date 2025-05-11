from django.contrib import admin
from myapp.models import Contact, Category, Team, Dish, Profile, Order, Shipper, DeliveryAddress, Delivery, DeliveryTracking, Restaurant, Cart, CartItem, OrderItem

admin.site.site_header = "FoodZone | Admin"

class ContactAdmin(admin.ModelAdmin):
    list_display = ['id','name','email','subject','added_on','is_approved']

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['id','name','added_on','updated_on']

class TeamAdmin(admin.ModelAdmin):
    list_display = ['id','name','added_on','updated_on']

class DishAdmin(admin.ModelAdmin):
    list_display = ['id','name','price','added_on','updated_on']

class ProfileAdmin(admin.ModelAdmin):
    list_display = ["user","contact_number"]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ["customer", "status", "ordered_on"]
    inlines = [OrderItemInline]

# Admin classes for delivery-related models
class ShipperAdmin(admin.ModelAdmin):
    list_display = ["user", "vehicle_type", "availability_status", "rating", "total_deliveries"]
    list_filter = ["availability_status", "vehicle_type"]
    search_fields = ["user__first_name", "user__last_name", "user__email", "vehicle_number"]

class DeliveryAddressAdmin(admin.ModelAdmin):
    list_display = ["customer", "address_line1", "city", "postal_code", "is_default"]
    list_filter = ["city", "is_default"]
    search_fields = ["customer__user__first_name", "address_line1", "city", "postal_code"]

class DeliveryTrackingInline(admin.TabularInline):
    model = DeliveryTracking
    extra = 0
    readonly_fields = ["timestamp"]

class DeliveryAdmin(admin.ModelAdmin):
    list_display = ["order", "shipper", "status", "estimated_delivery_time", "actual_delivery_time"]
    list_filter = ["status"]
    search_fields = ["order__customer__user__first_name", "shipper__user__first_name"]
    inlines = [DeliveryTrackingInline]

class DeliveryTrackingAdmin(admin.ModelAdmin):
    list_display = ["delivery", "status", "location", "timestamp"]
    list_filter = ["status"]
    search_fields = ["delivery__order__customer__user__first_name", "notes"]
    readonly_fields = ["timestamp"]

admin.site.register(Contact, ContactAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(Team, TeamAdmin )
admin.site.register(Dish, DishAdmin )
admin.site.register(Profile, ProfileAdmin)
admin.site.register(Order, OrderAdmin)

# Register delivery-related models
admin.site.register(Shipper, ShipperAdmin)
admin.site.register(DeliveryAddress, DeliveryAddressAdmin)
admin.site.register(Delivery, DeliveryAdmin)
admin.site.register(DeliveryTracking, DeliveryTrackingAdmin)
admin.site.register(Restaurant)

admin.site.register(Cart)
admin.site.register(CartItem)
admin.site.register(OrderItem)