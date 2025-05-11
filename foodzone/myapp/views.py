from django.shortcuts import render, get_object_or_404, reverse, redirect
from myapp.models import Contact, Dish, Team, Category, Profile, Order, Shipper, DeliveryAddress, Delivery, DeliveryTracking, DeliveryStatus, Restaurant, OrderStatus, DeliveryReview, Cart, CartItem, OrderItem
from myapp.forms import ShipperRegistrationForm, DeliveryAddressForm, UpdateDeliveryStatusForm, DeliveryTrackingForm, ShipperAvailabilityForm, RestaurantRegistrationForm, DeliveryReviewForm
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpResponseForbidden
from django.contrib.auth.models import User, Group
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from paypal.standard.forms import PayPalPaymentsForm
from django.conf import settings
from django.db.models import Q, Sum
from django.contrib import messages
from datetime import datetime, timedelta
import json
import uuid
import google.generativeai as genai
import requests
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

def index(request):
    context ={}
    cats = Category.objects.all().order_by('name')
    context['categories'] = cats
    # print()
    dishes = []
    for cat in cats:
        dishes.append({
            'cat_id':cat.id,
            'cat_name':cat.name,
            'cat_img':cat.image,
            'items':list(cat.dish_set.all().values())
        })
    context['menu'] = dishes
    return render(request,'index.html', context)

def contact_us(request):
    context={}
    if request.method=="POST":
        name = request.POST.get("name")
        em = request.POST.get("email")
        sub = request.POST.get("subject")
        msz = request.POST.get("message")
        
        obj = Contact(name=name, email=em, subject=sub, message=msz)
        obj.save()
        context['message']=f"Dear {name}, Thanks for your time!"

    return render(request,'contact.html', context)

def about(request):
    return render(request,'about.html')

def team_members(request):
    context={}
    members = Team.objects.all().order_by('name')
    context['team_members'] = members
    return render(request,'team.html', context)

def all_dishes(request):
    context={}
    dishes = Dish.objects.all()
    if "q" in request.GET:
        id = request.GET.get("q")
        dishes = Dish.objects.filter(category__id=id)
        context['dish_category'] = Category.objects.get(id=id).name 

    context['dishes'] = dishes
    return render(request,'all_dishes.html', context)

def register(request):
    context={}
    if request.method=="POST":
        #fetch data from html form
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('pass')
        contact = request.POST.get('number')
        check = User.objects.filter(username=email)
        if len(check)==0:
            #Save data to both tables
            usr = User.objects.create_user(email, email, password)
            usr.first_name = name
            usr.save()

            profile = Profile(user=usr, contact_number = contact)
            profile.save()
            
            context['status'] = f"User {name} Registered Successfully!"
        else:
            context['error'] = f"A User with this email already exists"

    return render(request,'register.html', context)

def check_user_exists(request):
    email = request.GET.get('usern')
    check = User.objects.filter(username=email)
    if len(check)==0:
        return JsonResponse({'status':0,'message':'Not Exist'})
    else:
        return JsonResponse({'status':1,'message':'A user with this email already exists!'})

def signin(request):
    context={}
    if request.method=="POST":
        email = request.POST.get('email')
        passw = request.POST.get('password')

        check_user = authenticate(username=email, password=passw)
        if check_user:
            login(request, check_user)
            if check_user.is_superuser or check_user.is_staff:
                return HttpResponseRedirect('/admin')
            return HttpResponseRedirect('/dashboard')
        else:
            context.update({'message':'Invalid Login Details!','class':'alert-danger'})

    return render(request,'login.html', context)

@login_required
def dashboard(request):
    if request.method == "POST":
        if "update_profile" in request.POST:
            name = request.POST.get('name')
            contact = request.POST.get('contact_number')
            address = request.POST.get('address')

            usr = User.objects.get(id=request.user.id)
            usr.first_name = name
            usr.save()

            # Tìm hoặc tạo profile cho người dùng
            profile, created = Profile.objects.get_or_create(
                user=usr,
                defaults={'contact_number': contact, 'address': address}
            )
            
            if not created:
                profile.contact_number = contact
                profile.address = address

            if "profile_pic" in request.FILES:
                pic = request.FILES['profile_pic']
                profile.profile_pic = pic
            profile.save()
            context = {'status': 'Profile updated successfully!'}

        elif "change_pass" in request.POST:
            c_password = request.POST.get('current_password')
            password = request.POST.get('new_password')

            check = authenticate(username=request.user.username, password=c_password)
            if check == None:
                context = {'status': 'Current password is wrong!'}
            else:
                usr = User.objects.get(id=request.user.id)
                usr.set_password(password)
                usr.save()
                login(request, usr)
                context = {'status': "Password updated successfully"}
        
        return render(request, 'dashboard.html', context)

    # Tìm hoặc tạo profile cho người dùng hiện tại
    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={'contact_number': ''}
    )
    
    # Lấy tất cả các đơn hàng của người dùng, sắp xếp theo thời gian giảm dần (mới nhất trước)
    orders = Order.objects.filter(customer=profile).order_by('-ordered_on')
    
    # Lấy danh sách địa chỉ giao hàng
    addresses = DeliveryAddress.objects.filter(customer=profile).order_by('-is_default')
    
    # Lấy danh sách đơn hàng đang chờ giao (chưa hoàn thành giao hàng)
    pending_orders = []
    for order in orders.filter(status=True):  # Chỉ lấy đơn hàng đã thanh toán
        try:
            delivery = Delivery.objects.get(order=order)
            if delivery.status != 'DE' and delivery.status != 'CA':  # Không phải đã giao hoặc đã hủy
                pending_orders.append(order)
        except Delivery.DoesNotExist:
            # Đơn hàng chưa có thông tin giao hàng
            pass
    
    # Lấy danh sách đơn hàng đã giao
    completed_orders = []
    for order in orders.filter(status=True):
        try:
            delivery = Delivery.objects.get(order=order)
            if delivery.status == 'DE':
                completed_orders.append(order)
        except Delivery.DoesNotExist:
            pass

    context = {
        'profile': profile,
        'orders': orders,  # Tất cả các đơn hàng
        'addresses': addresses,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'total_order': orders.count(),
        'success_order': orders.filter(status=True).count(),
        'pending_order': orders.filter(status=False).count()
    }
    
    return render(request, 'dashboard.html', context)

def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

def single_dish(request, id):
    context = {}
    dish = get_object_or_404(Dish, id=id)
    context['dish'] = dish
    
    if request.user.is_authenticated:
        if request.method == "POST":
            profile = Profile.objects.get(user=request.user)
            
            # Kiểm tra xem khách hàng có địa chỉ giao hàng không
            has_address = DeliveryAddress.objects.filter(customer=profile).exists()
            
            if not has_address:
                messages.error(request, "Bạn cần thêm địa chỉ giao hàng trước khi đặt hàng")
                return redirect('manage_addresses')
            
            # Tạo đơn hàng mới
            order = Order(customer=profile)
            order.save()
            
            # Tạo OrderItem cho món ăn này
            OrderItem.objects.create(
                order=order,
                dish=dish,
                quantity=1,
                price=dish.discounted_price
            )
            
            request.session['order_id'] = order.id
            
            host = request.get_host()
            paypal_dict = {
                'business': settings.PAYPAL_RECEIVER_EMAIL,
                'amount': dish.discounted_price,
                'item_name': f'Đơn hàng - {dish.name}',
                'invoice': str(uuid.uuid4()),
                'currency_code': 'USD',
                'notify_url': f'http://{host}{reverse("paypal-ipn")}',
                'return_url': f'http://{host}{reverse("payment_done")}',
                'cancel_return': f'http://{host}{reverse("payment_cancel")}',
            }
            form = PayPalPaymentsForm(initial=paypal_dict)
            context['form'] = form
            
    return render(request, "dish.html", context)

def payment_done(request):
    order_id = request.session.get('order_id')
    order = Order.objects.get(id=order_id)
    order.status = True
    order.save()
    
    # Tạo đơn hàng giao hàng
    try:
        profile = Profile.objects.get(user=request.user)
        # Lấy địa chỉ mặc định của khách hàng
        default_address = DeliveryAddress.objects.filter(customer=profile, is_default=True).first()
        
        if not default_address:
            # Nếu không có địa chỉ mặc định, thử lấy địa chỉ đầu tiên
            default_address = DeliveryAddress.objects.filter(customer=profile).first()
        
        if default_address:
            # Tính thời gian dự kiến giao hàng (1 giờ kể từ khi đặt hàng)
            est_delivery_time = datetime.now() + timedelta(hours=1)
            
            # Tìm người giao hàng đang rảnh - Đảm bảo lấy người giao hàng đầu tiên có trạng thái available
            available_shipper = Shipper.objects.filter(availability_status=True).first()
            
            if not available_shipper:
                # Nếu không tìm thấy shipper có sẵn, lấy shipper đầu tiên
                available_shipper = Shipper.objects.first()
            
            if available_shipper:
                # Tạo đơn hàng giao hàng
                delivery = Delivery.objects.create(
                    order=order,
                    shipper=available_shipper,
                    delivery_address=default_address,
                    status='CO',  # Sử dụng string chính xác thay vì DeliveryStatus.CONFIRMED
                    estimated_delivery_time=est_delivery_time,
                    delivery_notes="Đơn hàng mới từ thanh toán trực tuyến"
                )
                
                # Tạo log theo dõi đầu tiên
                DeliveryTracking.objects.create(
                    delivery=delivery,
                    status='CO',  # Sử dụng string chính xác thay vì DeliveryStatus.CONFIRMED 
                    notes="Đơn hàng đã được xác nhận và đang được chuẩn bị"
                )
                
                # In thông tin debug
                print(f"Created delivery: {delivery.id} for order: {order.id}, assigned to shipper: {available_shipper.user.username}")
            else:
                print("Error: No shippers available in the system")
        
    except Exception as e:
        # Xử lý lỗi (có thể ghi log hoặc thông báo cho admin)
        print(f"Error creating delivery: {str(e)}")
    
    return render(request, "payment_successfull.html")

def payment_cancel(request):
    ## remove comment to delete cancelled order
    # order_id = request.session.get('order_id')
    # Order.objects.get(id=order_id).delete()

    return render(request, 'payment_failed.html')

# Chức năng liên quan đến người giao hàng
def register_shipper(request):
    context = {}
    if request.method == "POST":
        form = ShipperRegistrationForm(request.POST)
        if form.is_valid():
            # Tạo User
            user_data = {
                'username': form.cleaned_data['email'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
            }
            user = User.objects.create_user(**user_data)
            
            # Tạo Shipper
            shipper = form.save(commit=False)
            shipper.user = user
            shipper.save()
            
            # Tạo Profile cho user để có thể truy cập dashboard
            profile = Profile(user=user, contact_number=form.cleaned_data.get('contact_number', ''))
            profile.save()
            
            context['status'] = f"Người giao hàng {user.first_name} đã đăng ký thành công! Vui lòng đăng nhập."
            return redirect('login')
        else:
            context['form'] = form
    else:
        form = ShipperRegistrationForm()
        context['form'] = form
    
    return render(request, 'register_shipper.html', context)

@login_required
def shipper_dashboard(request):
    context = {}
    try:
        shipper = Shipper.objects.get(user=request.user)
        context['shipper'] = shipper
        
        # Debug: In thông tin shipper
        print(f"Shipper: {shipper.user.username} (ID: {shipper.id})")
        
        # Lấy tất cả đơn giao hàng của shipper (không lọc status)
        all_deliveries = Delivery.objects.filter(shipper=shipper)
        
        # Debug: In ra tất cả đơn hàng tìm thấy
        print(f"Found {all_deliveries.count()} deliveries for this shipper")
        for d in all_deliveries:
            print(f"  - Delivery ID: {d.id}, Order ID: {d.order.id}, Status: {d.status}")
        
        # Get active deliveries - chỉ lấy đơn có status đang thực hiện
        active_deliveries = all_deliveries.filter(
            status__in=['CO', 'PR', 'RP', 'PU', 'OW']
        ).order_by('created_at')
        
        # Get completed deliveries
        completed_deliveries = all_deliveries.filter(
            status='DE'  # Đã giao hàng
        ).order_by('-actual_delivery_time')[:10]
        
        context['active_deliveries'] = active_deliveries
        context['completed_deliveries'] = completed_deliveries
        
        # Debug: In số lượng đơn active để xác nhận
        print(f"Active deliveries: {active_deliveries.count()}")
        print(f"Completed deliveries: {completed_deliveries.count()}")
        
        # Availability form
        if request.method == "POST":
            form = ShipperAvailabilityForm(request.POST, instance=shipper)
            if form.is_valid():
                form.save()
                messages.success(request, "Trạng thái của bạn đã được cập nhật!")
        else:
            form = ShipperAvailabilityForm(instance=shipper)
        
        context['availability_form'] = form
        
        # Đảm bảo profile tồn tại cho người dùng hiện tại
        profile, created = Profile.objects.get_or_create(
            user=request.user,
            defaults={'contact_number': ''}
        )
        
    except Shipper.DoesNotExist:
        context['error'] = "Bạn không phải là người giao hàng"
        print("Error: User is not a shipper")
    
    return render(request, 'shipper_dashboard.html', context)

@login_required
def update_delivery_status(request, delivery_id):
    if request.method == "POST":
        try:
            shipper = Shipper.objects.get(user=request.user)
            delivery = get_object_or_404(Delivery, id=delivery_id, shipper=shipper)
            
            form = UpdateDeliveryStatusForm(request.POST, instance=delivery)
            if form.is_valid():
                updated_delivery = form.save()
                
                # Create tracking log
                tracking_form = DeliveryTrackingForm(request.POST)
                if tracking_form.is_valid():
                    DeliveryTracking.objects.create(
                        delivery=delivery,
                        status=updated_delivery.status,
                        location=tracking_form.cleaned_data['location'],
                        notes=tracking_form.cleaned_data['notes']
                    )
                
                # Update actual delivery time if delivered
                if updated_delivery.status == DeliveryStatus.DELIVERED:
                    updated_delivery.actual_delivery_time = datetime.now()
                    updated_delivery.save()
                    
                    # Update shipper stats
                    shipper.total_deliveries += 1
                    shipper.save()
                
                messages.success(request, "Cập nhật trạng thái đơn hàng thành công!")
                return redirect('shipper_dashboard')
            else:
                messages.error(request, "Lỗi cập nhật trạng thái đơn hàng")
        except Shipper.DoesNotExist:
            messages.error(request, "Bạn không có quyền cập nhật đơn hàng này")
    
    return redirect('shipper_dashboard')

@login_required
def delivery_detail(request, delivery_id):
    context = {}
    try:
        shipper = Shipper.objects.get(user=request.user)
        delivery = get_object_or_404(Delivery, id=delivery_id, shipper=shipper)
        
        context['delivery'] = delivery
        context['tracking_logs'] = delivery.tracking_logs.all().order_by('-timestamp')
        context['status_form'] = UpdateDeliveryStatusForm(instance=delivery)
        context['tracking_form'] = DeliveryTrackingForm(initial={
            'status': delivery.status,
            'location': shipper.current_location
        })
        
        return render(request, 'delivery_detail.html', context)
    except Shipper.DoesNotExist:
        messages.error(request, "Bạn không có quyền xem đơn hàng này")
        return redirect('login')

# Chức năng quản lý giao hàng cho khách hàng
@login_required
def manage_addresses(request):
    context = {}
    try:
        profile = Profile.objects.get(user=request.user)
        addresses = DeliveryAddress.objects.filter(customer=profile)
        
        if request.method == "POST":
            form = DeliveryAddressForm(request.POST)
            if form.is_valid():
                address = form.save(commit=False)
                address.customer = profile
                
                # Check if this is the first address or marked as default
                if form.cleaned_data['is_default'] or not addresses.exists():
                    # Set all other addresses to non-default
                    addresses.update(is_default=False)
                
                address.save()
                messages.success(request, "Địa chỉ mới đã được lưu!")
                return redirect('manage_addresses')
        else:
            form = DeliveryAddressForm()
        
        context['addresses'] = addresses
        context['form'] = form
        
        return render(request, 'manage_addresses.html', context)
    except Profile.DoesNotExist:
        messages.error(request, "Bạn cần đăng nhập để quản lý địa chỉ")
        return redirect('login')

@login_required
def delete_address(request, address_id):
    if request.method == "POST":
        try:
            profile = Profile.objects.get(user=request.user)
            address = get_object_or_404(DeliveryAddress, id=address_id, customer=profile)
            
            # If this was the default address, set another one as default
            if address.is_default:
                other_address = DeliveryAddress.objects.filter(customer=profile).exclude(id=address_id).first()
                if other_address:
                    other_address.is_default = True
                    other_address.save()
            
            address.delete()
            messages.success(request, "Địa chỉ đã được xóa thành công")
        except Profile.DoesNotExist:
            messages.error(request, "Bạn không có quyền xóa địa chỉ này")
    
    return redirect('manage_addresses')

@login_required
def set_default_address(request, address_id):
    if request.method == "POST":
        try:
            profile = Profile.objects.get(user=request.user)
            
            # Set all addresses to non-default
            DeliveryAddress.objects.filter(customer=profile).update(is_default=False)
            
            # Set the selected address as default
            address = get_object_or_404(DeliveryAddress, id=address_id, customer=profile)
            address.is_default = True
            address.save()
            
            messages.success(request, "Địa chỉ mặc định đã được cập nhật")
        except Profile.DoesNotExist:
            messages.error(request, "Bạn không có quyền thực hiện hành động này")
    
    return redirect('manage_addresses')

@login_required
def track_order(request, order_id):
    context = {}
    from .forms import DeliveryReviewForm
    from .models import DeliveryReview
    try:
        profile = Profile.objects.get(user=request.user)
        order = get_object_or_404(Order, id=order_id, customer=profile)
        try:
            delivery = Delivery.objects.get(order=order)
            tracking_logs = delivery.tracking_logs.all().order_by('-timestamp')
            
            # Tính tổng giá trị đơn hàng từ OrderItem
            order_items = OrderItem.objects.filter(order=order)
            total_amount = sum(item.price * item.quantity for item in order_items)
            
            context['order'] = order
            context['delivery'] = delivery
            context['tracking_logs'] = tracking_logs
            context['total_amount'] = total_amount
            context['order_items'] = order_items
            
            # Nếu đơn đã giao, cho phép đánh giá
            review = None
            if delivery.status == 'DE':
                try:
                    review = DeliveryReview.objects.get(delivery=delivery, customer=profile)
                except DeliveryReview.DoesNotExist:
                    review = None
                # Nếu đã có review, không cho submit nữa
                if review:
                    context['review'] = review
                elif request.method == 'POST' and 'submit_review' in request.POST:
                    review_form = DeliveryReviewForm(request.POST)
                    if review_form.is_valid():
                        new_review = review_form.save(commit=False)
                        new_review.delivery = delivery
                        new_review.customer = profile
                        new_review.save()
                        context['review'] = new_review
                        context['review_submitted'] = True
                    else:
                        context['review_form'] = review_form
                else:
                    context['review_form'] = DeliveryReviewForm()
            return render(request, 'track_order.html', context)
        except Delivery.DoesNotExist:
            # Tính tổng giá trị đơn hàng từ OrderItem
            order_items = OrderItem.objects.filter(order=order)
            total_amount = sum(item.price * item.quantity for item in order_items)
            
            context['order'] = order
            context['message'] = "Đơn hàng của bạn chưa được xử lý giao hàng"
            context['total_amount'] = total_amount
            context['order_items'] = order_items
            return render(request, 'track_order.html', context)
    except Profile.DoesNotExist:
        messages.error(request, "Bạn không có quyền xem đơn hàng này")
        return redirect('login')

# API để cập nhật vị trí hiện tại của người giao hàng
@login_required
def update_location(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            location_name = data.get('location_name', '')
            
            if latitude and longitude:
                shipper = Shipper.objects.get(user=request.user)
                location_str = f"{location_name} ({latitude}, {longitude})"
                shipper.current_location = location_str
                shipper.save()
                
                # Update any active deliveries being handled by this shipper
                active_deliveries = Delivery.objects.filter(
                    shipper=shipper,
                    status=DeliveryStatus.ON_THE_WAY
                )
                
                for delivery in active_deliveries:
                    DeliveryTracking.objects.create(
                        delivery=delivery,
                        status=DeliveryStatus.ON_THE_WAY,
                        location=location_str,
                        notes="Cập nhật vị trí tự động"
                    )
                
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'})

def is_restaurant_owner(user):
    return hasattr(user, 'restaurant') and user.restaurant is not None

@login_required
def restaurant_dashboard(request):
    context = {}
    
    try:
        # Get restaurant owned by current user
        restaurant = Restaurant.objects.get(owner=request.user)
        
        # Get orders for this restaurant, looking at OrderItem
        order_items = OrderItem.objects.filter(
            dish__restaurant=restaurant
        ).select_related('order').exclude(
            order__status=False
        ).order_by('-order__ordered_on')
        
        # Get unique orders
        order_ids = order_items.values_list('order_id', flat=True).distinct()
        orders = Order.objects.filter(id__in=order_ids)
        
        # Get completed orders
        completed_order_items = OrderItem.objects.filter(
            dish__restaurant=restaurant,
            order__status=True
        ).select_related('order').order_by('-order__ordered_on')[:10]
        
        completed_order_ids = completed_order_items.values_list('order_id', flat=True).distinct()
        completed_orders = Order.objects.filter(id__in=completed_order_ids)
        
        # Get deliveries for orders from this restaurant
        deliveries = Delivery.objects.filter(
            order__id__in=order_ids
        ).exclude(
            status=DeliveryStatus.DELIVERED
        ).order_by('-created_at')
        
        order_count = orders.count()
        
        # Calculate revenue from completed orders
        revenue = sum(item.price * item.quantity for item in completed_order_items)
        
        context.update({
            'restaurant': restaurant,
            'orders': orders,
            'order_items': order_items,
            'completed_orders': completed_orders,
            'completed_order_items': completed_order_items,
            'deliveries': deliveries,
            'order_count': order_count,
            'revenue': revenue
        })
        
        # Đảm bảo profile tồn tại cho người dùng hiện tại
        profile, created = Profile.objects.get_or_create(
            user=request.user,
            defaults={'contact_number': ''}
        )
        
    except Restaurant.DoesNotExist:
        # Redirect to restaurant creation form if user doesn't have a restaurant
        context['restaurant_error'] = "Bạn chưa đăng ký nhà hàng. Vui lòng tạo nhà hàng của bạn."
    
    return render(request, 'restaurant_dashboard.html', context)

def chatbot(request):
    return render(request, 'chatbot.html')

@csrf_exempt
def chatbot_query(request):
    if request.method == 'POST':
        try:
            # Parse the JSON data from the request
            data = json.loads(request.body)
            user_message = data.get('message', '')
            
            # Initialize the Gemini API with your API key
            genai.configure(api_key="AIzaSyCkoGNqZt1dwmhH5w-GGE57FqmFo7399_4")
            
            # Get menu data to provide context to the AI
            dishes = Dish.objects.filter(is_available=True)
            team_members = Team.objects.all()
            
            # Create context about the restaurant, menu and team
            context = "Thông tin về nhà hàng FoodZone:\n"
            
            # Add dish information
            context += "\nDanh sách món ăn:\n"
            for dish in dishes:
                context += f"- {dish.name}: {dish.price} đồng"
                if dish.discounted_price:
                    context += f" (giảm giá: {dish.discounted_price} đồng)"
                context += f". Thành phần: {dish.ingredients}\n"
            
            # Add team information
            context += "\nĐội ngũ đầu bếp:\n"
            for member in team_members:
                context += f"- {member.name}: {member.designation}\n"
            
            # Set up the model
            generation_config = {
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 0,
                "max_output_tokens": 1024,
            }
            
            model = genai.GenerativeModel(
                model_name="gemini-1.5-pro",
                generation_config=generation_config
            )
            
            # Create the prompt with instructions for the AI
            prompt = f"""
            Bạn là trợ lý ảo của nhà hàng FoodZone. Hãy trả lời các câu hỏi của khách hàng về thực đơn, giá cả, 
            thành phần món ăn, đội ngũ đầu bếp, và các thông tin khác về nhà hàng.
            
            Hãy trả lời bằng tiếng Việt, thân thiện và hữu ích. Nếu không biết câu trả lời, hãy đề nghị khách hàng 
            liên hệ với nhà hàng qua số điện thoại hoặc email.
            
            Dưới đây là thông tin về nhà hàng để bạn tham khảo khi trả lời:
            {context}
            
            Câu hỏi của khách hàng: {user_message}
            """
            
            # Generate response
            response = model.generate_content(prompt)
            
            # Return the response as JSON
            return JsonResponse({'response': response.text})
        
        except Exception as e:
            # Log the error (in a production environment)
            print(f"Error in chatbot query: {str(e)}")
            return JsonResponse({'response': 'Xin lỗi, đã xảy ra lỗi khi xử lý yêu cầu của bạn. Vui lòng thử lại sau.'}, status=500)
    
    # Handle non-POST requests
    return JsonResponse({'error': 'Phương thức không được hỗ trợ'}, status=405)

def register_restaurant(request):
    context = {}
    if request.method == "POST":
        form = RestaurantRegistrationForm(request.POST)
        if form.is_valid():
            # Tạo User
            user_data = {
                'username': form.cleaned_data['email'],
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
                'first_name': form.cleaned_data['first_name'],
                'last_name': form.cleaned_data['last_name'],
            }
            user = User.objects.create_user(**user_data)
            
            # Tạo Restaurant
            restaurant = form.save(commit=False)
            restaurant.owner = user
            restaurant.save()
            
            # Tạo Profile cho user để có thể truy cập dashboard
            profile = Profile(user=user, contact_number=form.cleaned_data.get('contact_number', ''))
            profile.save()
            
            context['status'] = f"Nhà hàng {restaurant.name} đã được đăng ký thành công! Vui lòng đăng nhập."
            return redirect('login')
        else:
            context['form'] = form
    else:
        form = RestaurantRegistrationForm()
        context['form'] = form
    
    return render(request, 'register_restaurant.html', context)

@require_POST
def add_to_cart(request, dish_id):
    dish = get_object_or_404(Dish, id=dish_id)
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key or request.session.create()
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    item, created = CartItem.objects.get_or_create(cart=cart, dish=dish)
    if not created:
        item.quantity += 1
        item.save()
    return redirect('view_cart')

def view_cart(request):
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
    else:
        session_key = request.session.session_key
        cart = Cart.objects.filter(session_key=session_key).first()
    
    items = cart.items.all() if cart else []
    
    # Tính tổng tiền
    total_price = 0
    for item in items:
        total_price += item.dish.price * item.quantity
    
    context = {
        'cart': cart,
        'items': items,
        'total_price': total_price
    }
    
    return render(request, 'cart.html', context)

@require_POST
def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    return redirect('view_cart')

@require_POST
def update_quantity(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            # Nếu số lượng về 0 thì xóa món khỏi giỏ
            cart_item.delete()
            return redirect('view_cart')
    
    cart_item.save()
    return redirect('view_cart')

@login_required
def checkout_cart(request):
    if request.method == "POST":
        profile = Profile.objects.get(user=request.user)
        cart = Cart.objects.filter(user=request.user).first()
        
        if not cart or not cart.items.exists():
            messages.error(request, "Giỏ hàng của bạn đang trống!")
            return redirect('view_cart')
        
        # Kiểm tra xem người dùng có địa chỉ giao hàng không
        has_address = DeliveryAddress.objects.filter(customer=profile).exists()
        if not has_address:
            messages.error(request, "Bạn cần thêm địa chỉ giao hàng trước khi đặt hàng")
            return redirect('manage_addresses')
        
        # Tạo một đơn hàng duy nhất cho tất cả các món
        order = Order(
            customer=profile,
            status=False  # Chưa thanh toán
        )
        order.save()
        
        # Tính tổng tiền
        total_amount = 0
        
        # Tạo OrderItem cho từng món trong giỏ
        for cart_item in cart.items.all():
            item_price = cart_item.dish.discounted_price
            item_total = item_price * cart_item.quantity
            total_amount += item_total
            
            # Tạo OrderItem
            OrderItem.objects.create(
                order=order,
                dish=cart_item.dish,
                quantity=cart_item.quantity,
                price=item_price
            )
        
        # Lưu thông tin đơn hàng vào session
        request.session['order_id'] = order.id
        request.session['cart_id'] = cart.id
        
        # Chuyển đến trang thanh toán PayPal
        return redirect('process_cart_payment')
        
    # Nếu không phải POST hoặc không có món nào trong giỏ
    return redirect('view_cart')

def process_cart_payment(request):
    # Lấy thông tin đơn hàng từ session
    order_id = request.session.get('order_id')
    
    if not order_id:
        messages.error(request, "Không tìm thấy thông tin đơn hàng!")
        return redirect('view_cart')
    
    try:
        order = Order.objects.get(id=order_id)
        order_items = OrderItem.objects.filter(order=order)
        
        if not order_items.exists():
            messages.error(request, "Đơn hàng không có món ăn nào!")
            return redirect('view_cart')
        
        # Tính tổng tiền
        total_amount = sum(item.price * item.quantity for item in order_items)
        
        # Tạo danh sách tên món
        item_names = [f"{item.dish.name} x{item.quantity}" for item in order_items]
        
        host = request.get_host()
        
        # Tạo payload cho PayPal
        paypal_dict = {
            'business': settings.PAYPAL_RECEIVER_EMAIL,
            'amount': total_amount,
            'item_name': f'Đơn hàng FoodZone #{order.id}',
            'invoice': str(uuid.uuid4()),
            'currency_code': 'USD',
            'notify_url': f'http://{host}{reverse("paypal-ipn")}',
            'return_url': f'http://{host}{reverse("cart_payment_done")}',
            'cancel_return': f'http://{host}{reverse("cart_payment_cancel")}',
        }
        
        # Tạo form thanh toán PayPal
        form = PayPalPaymentsForm(initial=paypal_dict)
        context = {
            'form': form,
            'order': order,
            'order_items': order_items,
            'total_amount': total_amount,
            'item_names': item_names
        }
        
        return render(request, 'process_cart_payment.html', context)
        
    except Order.DoesNotExist:
        messages.error(request, "Đơn hàng không tồn tại!")
        return redirect('view_cart')

def cart_payment_done(request):
    # Lấy thông tin đơn hàng từ session
    order_id = request.session.get('order_id')
    cart_id = request.session.get('cart_id')
    
    if not order_id:
        messages.error(request, "Không tìm thấy thông tin đơn hàng!")
        return redirect('view_cart')
    
    try:
        # Cập nhật trạng thái đơn hàng
        order = Order.objects.get(id=order_id)
        order.status = True  # Đã thanh toán
        order.save()
        
        # Tạo thông tin giao hàng
        try:
            profile = Profile.objects.get(user=request.user)
            default_address = DeliveryAddress.objects.filter(customer=profile, is_default=True).first() or DeliveryAddress.objects.filter(customer=profile).first()
            
            if default_address:
                est_delivery_time = datetime.now() + timedelta(hours=1)
                available_shipper = Shipper.objects.filter(availability_status=True).first() or Shipper.objects.first()
                
                if available_shipper:
                    delivery = Delivery.objects.create(
                        order=order,
                        shipper=available_shipper,
                        delivery_address=default_address,
                        status='CO',  # Đã xác nhận
                        estimated_delivery_time=est_delivery_time,
                        delivery_notes="Đơn hàng mới từ thanh toán giỏ hàng"
                    )
                    
                    DeliveryTracking.objects.create(
                        delivery=delivery,
                        status='CO',
                        notes="Đơn hàng đã được xác nhận và đang được chuẩn bị"
                    )
        except Exception as e:
            print(f"Error creating delivery: {str(e)}")
        
        # Xóa giỏ hàng sau khi đã thanh toán thành công
        if cart_id:
            try:
                cart = Cart.objects.get(id=cart_id)
                cart.items.all().delete()
            except Cart.DoesNotExist:
                pass
        
        # Xóa session
        if 'order_id' in request.session:
            del request.session['order_id']
        if 'cart_id' in request.session:
            del request.session['cart_id']
        
        return render(request, 'payment_successfull.html')
        
    except Order.DoesNotExist:
        messages.error(request, "Đơn hàng không tồn tại!")
        return redirect('view_cart')

def cart_payment_cancel(request):
    # Không xóa đơn hàng, để người dùng có thể thử lại
    return render(request, 'payment_failed.html')
