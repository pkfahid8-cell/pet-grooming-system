import base64

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.files.base import ContentFile
from django.db.models import Avg, Min, Sum
from django.db.models import Avg, Min
from django.db.models.functions import Cast
from django.db.models import FloatField
from django.core.files.storage import FileSystemStorage
from django.http import request, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from datetime import datetime
from django.utils import timezone
import cloudinary.uploader

from django.contrib.auth.models import User, Group
from django.views.decorators.csrf import csrf_exempt

from myapp.models import Staff, customer, Complaints, Product, GroomingService, Review, GroomingBooking, cart, \
    OderSub, OderMain, Category, ShippingAddress, PetType, Wishlist
from decimal import Decimal

from django.contrib.auth.decorators import login_required


# ---------------------------------------------
# LOGIN
# ---------------------------------------------

def login_get(request):
    return render(request, 'login.html')


def login_post(request):
    username = request.POST['username']
    password = request.POST['password']

    user = authenticate(request, username=username, password=password)

    if user is not None:
        login(request, user)

        if user.is_superuser or user.groups.filter(name='admin').exists():
            return redirect('/myapp/adminhome')

        elif user.groups.filter(name='staff').exists():
            staff = Staff.objects.get(AUTHUSER=user)

            if staff.status == 'approved':
                return redirect('/myapp/shophome')
            else:
                return redirect('/myapp/login_get')

    return redirect('/myapp/login_get')


# user
@csrf_exempt
def login_(request):
    if request.method != "POST":
        return JsonResponse({"status": "error"})

    email = request.POST.get("email")
    password = request.POST.get("password")

    user = authenticate(request, username=email, password=password)

    if user is None:
        return JsonResponse({"status": "no"})

    # 🔥 GET CUSTOMER OBJECT
    try:
        cust = customer.objects.get(AUTHUSER=user)
    except customer.DoesNotExist:
        return JsonResponse({"status": "no"})

    return JsonResponse({
        "status": "ok",
        "auth_id": user.id,  # optional
        "customer_id": cust.id  # 🔥 IMPORTANT
    })


def logout_get(request):
    logout(request)
    return redirect('/myapp/login_get')


# ---------------------------------------------
# ADMIN
# ---------------------------------------------

@login_required(login_url='/myapp/login_get')
def adminhome(request):
    return render(request, 'admin/admin_index.html')


@login_required(login_url='/myapp/login_get')
def Approve_shop(request, shop_id):
    shop = Staff.objects.get(id=shop_id)
    shop.status = 'approved'
    shop.save()
    return redirect('/myapp/view_shop')


def add_pet_type_get(request):
    return render(request, 'admin/add_pettype.html')


def add_pet_post(request):
    pet_name = request.POST['petname']
    pet = PetType()
    pet.pet_type = pet_name
    pet.save()
    return redirect('/myapp/add_pet_type_get/')

@login_required(login_url='/myapp/login_get')
def admin_generate_report(request):

    from_date = request.GET.get('from')
    to_date = request.GET.get('to')

    # Only delivered orders
    orders = OderMain.objects.filter(status="delivered")
    bookings = GroomingBooking.objects.filter(status="completed")

    # Date filter (works only if date stored as YYYY-MM-DD string)
    if from_date and to_date:
        orders = orders.filter(date__range=[from_date, to_date])
        bookings = bookings.filter(date__range=[from_date, to_date])

    # Convert total_amount to integer sum safely
    total_sales = 0
    for o in orders:
        total_sales += int(o.total_amount)

    total_orders = orders.count()
    total_grooming = bookings.count()

    return render(request, 'admin/admin_report.html', {
        'orders': orders,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_grooming': total_grooming
    })




@login_required(login_url='/myapp/login_get')
def view_rating_review(request):
    Reviews = Review.objects.all()
    return render(request, 'admin/View review about Shops.html', {'data': Reviews})


@login_required(login_url='/myapp/login_get')
def Reject_shop(request, shop_id):
    shop = Staff.objects.get(id=shop_id)
    shop.status = 'Rejected'
    shop.save()
    return redirect('/myapp/view_shop')


@login_required(login_url='/myapp/login_get')
def view_shop(request):
    shop = Staff.objects.all()
    return render(request, 'admin/View shop.html', {'data': shop})


@login_required(login_url='/myapp/login_get')
# def view_approved_and_rejected(request):
#     approved = Staff.objects.filter(status="approved")
#     rejected = Staff.objects.filter(status="rejected")
#     return render(request, "Admin/view approved and rejected shop.html", {
#         "approved": approved,
#         "rejected": rejected
#     })

def view_approved_and_rejected(request):
    approved = Staff.objects.filter(status="approved")
    rejected = Staff.objects.filter(status="Rejected")

    return render(
        request,
        "admin/view approved and rejected shop.html",
        {
            "approved": approved,
            "rejected": rejected,
        },
    )

@login_required(login_url='/myapp/login_get')
def view_cutomer(request):
    user = customer.objects.all()
    return render(request, 'admin/View Customer.html', {'data': user})


@login_required(login_url='/myapp/login_get')
def view_approved_shop(request):
    shop = Staff.objects.filter(status='approved')
    return render(request, 'admin/View approved shop.html', {'data': shop})


@login_required(login_url='/myapp/login_get')
def view_Rejected_shop(request):
    shop = Staff.objects.filter(status='Rejected')
    return render(request, 'admin/View rejected shop.html', {'data': shop})


@login_required(login_url='/myapp/login_get')
def view_complaint(request):
    com = Complaints.objects.all()
    return render(request, 'admin/View complaints and Send reply.html', {'data': com})


@login_required(login_url='/myapp/login_get')
def send_reply_get(request, cus_id):
    a = Complaints.objects.get(id=cus_id)
    return render(request, 'admin/Send reply.html', {'a': a})


@login_required(login_url='/myapp/login_get')
def send_reply(request):
    cus_id = request.POST['cus_id']
    complaint = Complaints.objects.get(id=cus_id)
    reply = request.POST['reply']
    complaint.status = 'replied'
    complaint.reply = reply
    complaint.save()
    return redirect('/myapp/view_complaint')


@login_required(login_url='/myapp/login_get')
def add_product_get(request):
    categories = Category.objects.all()
    return render(request, 'admin/Add product.html', {'categories': categories})


@login_required(login_url='/myapp/login_get')
def add_product_post(request):
    pname = request.POST['pname']
    brand_name = request.POST['brand_name']
    category_id = request.POST['Category']
    quantity = request.POST['Quantity']
    description = request.POST['description']
    price = request.POST['price']
    image = request.FILES['image']

    category_obj = Category.objects.get(id=category_id)

    fs = FileSystemStorage()
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + image.name
    fs.save(filename, image)
    image_path = fs.url(filename)

    product = Product()
    product.CATEGORY = category_obj
    product.pname = pname
    product.brand_name = brand_name
    product.Quantity = quantity
    product.description = description
    product.price = price
    product.image = image_path
    product.status = "available"
    product.save()

    return redirect('/myapp/adminhome')


@login_required(login_url='/myapp/login_get')
def View_product(request):
    Products = Product.objects.all()
    return render(request, 'admin/View Products.html', {'Products': Products})


def edit_product_get(request, pro_id):
    Products = Product.objects.get(id=pro_id)
    cat = Category.objects.all()
    return render(request, 'admin/Edit Product.html', {
        'data': Products,
        'categories': cat
    })


def edit_product_post(request):
    pro_id = request.POST['pro_id']
    product = Product.objects.get(id=pro_id)

    product.pname = request.POST['pname']
    product.brand_name = request.POST['brand_name']
    product.Category = request.POST['Category']

    # ✅ Quantity as INTEGER
    qty = int(request.POST['Quantity'])
    product.Quantity = qty

    product.description = request.POST['description']
    product.price = request.POST['price']

    # ✅ AUTO STATUS LOGIC
    if qty == 0:
        product.status = "sold Out"
    elif qty <= 5:
        product.status = "low Stock"
    else:
        product.status = "available"

    # ✅ Safe image handling
    image = request.FILES.get('image')
    if image:
        fs = FileSystemStorage()
        d = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = d + "_img.jpg"
        fs.save(image_filename, image)
        product.image = fs.url(image_filename)

    product.save()
    return redirect('/myapp/View_product/')


def delete_product(request, pro_id):
    Product.objects.get(id=pro_id).delete()
    return redirect('/myapp/View_product')


@login_required(login_url='/myapp/login_get')
def view_grooming(request):
    grooming = GroomingService.objects.all()
    return render(request, 'admin/View grooming services.html', {'data': grooming})


@login_required(login_url='/myapp/login_get')
def add_grooming_get(request):
    return render(request, 'admin/Add grooming.html')


@login_required(login_url='/myapp/login_get')
def add_grooming_post(request):
    service_name = request.POST['service_name']
    description = request.POST['description']
    price = request.POST['price']
    image = request.FILES['image']
    time = request.POST['time']

    fs = FileSystemStorage()
    filename = datetime.now().strftime("%Y%m%d_%H%M%S") + image.name
    fs.save(filename, image)
    image_path = fs.url(filename)

    grooming = GroomingService()
    grooming.service_name = service_name
    grooming.description = description
    grooming.price = price
    grooming.time = time
    grooming.image = image_path
    grooming.save()

    return redirect('/myapp/adminhome')


@login_required(login_url='/myapp/login_get')
def edit_grooming_services_get(request, groom_id):
    grooming = GroomingService.objects.get(id=groom_id)
    return render(request, 'admin/Edit grooming service.html', {'grooming': grooming})


@login_required(login_url='/myapp/login_get')
def edit_grooming_services_post(request):
    groom_id = request.POST['groom_id']
    groom = GroomingService.objects.get(id=groom_id)

    groom.service_name = request.POST['service_name']
    groom.description = request.POST['description']
    groom.price = request.POST['price']
    groom.time = request.POST['time']

    if 'image' in request.FILES:
        image = request.FILES['image']
        fs = FileSystemStorage()
        d = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = d + "_img.jpg"
        fs.save(image_filename, image)
        groom.image = fs.url(image_filename)

    groom.save()
    return redirect('/myapp/view_grooming')


@login_required(login_url='/myapp/login_get')
def delete_groomigs_service(request, groom_id):
    GroomingService.objects.filter(id=groom_id).delete()
    return redirect('/myapp/view_grooming')


@login_required(login_url='/myapp/login_get')
def change_password_admin(request):
    return render(request, 'admin/change password admin.html')


@login_required(login_url='/myapp/login_get')
def change_password_admin_post(request):
    Old_Password = request.POST['Old_Password']
    New_password = request.POST['New_password']
    Confirm_password = request.POST['Confirm_password']
    if not request.user.check_password(Old_Password):
        return render(request, 'admin/change password admin.html', {'error': 'Current password is incorrect'})
    if New_password != Confirm_password:
        return render(request, 'admin/change password admin.html', {'error': 'New passwords do not match'})
    request.user.set_password(New_password)
    request.user.save()
    return redirect('/myapp/login_get')


@login_required(login_url='/myapp/login_get')
def view_delivery_address(request):
    orders = OderMain.objects.select_related('USER', 'ADDRESS')

    return render(request, 'admin/View delivery address.html', {
        'orders': orders
    })


# ---------------------------------------------
# SHOP REGISTRATION (NO LOGIN REQUIRED)
# ---------------------------------------------
def Staff_registration_get(request):
    return render(request, 'Staff/Staff registartion.html')

def Staff_registration_Post(request):
    name = request.POST['name']
    place = request.POST['place']
    pin = request.POST['pin']
    post = request.POST['post']
    phone = request.POST['phone_no']
    password = request.POST['password']
    profile_img = request.FILES['profile']

    if (
        User.objects.filter(username__iexact=name).exists() or
        Staff.objects.filter(phone_no=phone).exists()
    ):
        return render(request, 'Staff/Staff registartion.html')

    # Upload image to Cloudinary
    result = cloudinary.uploader.upload(profile_img)
    profile_path = result["secure_url"]

    authuser = User.objects.create_user(
        username=name,
        password=password,
        first_name=name
    )

    staff_group = Group.objects.get(name='staff')
    authuser.groups.add(staff_group)
    authuser.save()

    s = Staff()
    s.AUTHUSER = authuser
    s.name = name
    s.place = place
    s.pin = pin
    s.post = post
    s.phone_no = phone
    s.profile = profile_path
    s.save()

    return redirect('/myapp/login_get')
# def Staff_registration_Post(request):
#     name = request.POST['name']
#     place = request.POST['place']
#     pin = request.POST['pin']
#     post = request.POST['post']
#     phone = request.POST['phone_no']
#     password = request.POST['password']
#     profile_img = request.FILES['profile']

#     if (
#                 User.objects.filter(username__iexact=name).exists() or
#                 Staff.objects.filter(phone_no=phone).exists()
#     ):
#         return render(request, 'Staff/Staff registartion.html')

#     f = FileSystemStorage()
#     d = datetime.now().strftime("%Y%m%d_%H%M%S")
#     filename = d + "_staff.jpg"
#     f.save(filename, profile_img)
#     profile_path = f.url(filename)

#     authuser = User.objects.create_user(
#         username=name,
#         password=password,
#         first_name=name
#     )

#     staff_group = Group.objects.get(name='staff')
#     authuser.groups.add(staff_group)
#     authuser.save()

#     s = Staff()
#     s.AUTHUSER = authuser
#     s.name = name
#     s.place = place
#     s.pin = pin
#     s.post = post
#     s.phone_no = phone
#     s.profile = profile_path
#     s.save()

#     return redirect('/myapp/login_get')


def check_staff_exists(request):
    field = request.GET.get('field')
    value = request.GET.get('value')

    exists = False

    if field == "name":
        exists = User.objects.filter(username__iexact=value).exists()
    elif field == "email":
        exists = User.objects.filter(email__iexact=value).exists()
    elif field == "phone_no":
        exists = Staff.objects.filter(phone_no=value).exists()

    return JsonResponse({"exists": exists})


# ---------------------------------------------
# SHOP PROTECTED VIEWS
# ---------------------------------------------

@login_required(login_url='/myapp/login_get')
def shophome(request):
    return render(request, 'Staff/shop_index.html')


@login_required(login_url='/myapp/login_get')
def change_password_shop_get(request):
    return render(request, 'Staff/Change password.html')


@login_required(login_url='/myapp/login_get')
def change_password_shop_post(request):
    Old_Password = request.POST['Old_Password']
    New_password = request.POST['New_password']
    Confirm_password = request.POST['Confirm_password']
    if not request.user.check_password(Old_Password):
        return render(request, 'Staff/Change password.html', {'error': 'Current password is incorrect'})
    if New_password != Confirm_password:
        return render(request, 'Staff/Change password.html', {'error': 'New passwords do not match'})
    request.user.set_password(New_password)
    request.user.save()
    return redirect('/myapp/login_get')


def add_category_get(request):
    return render(request, 'admin/Catogery.html')


@login_required(login_url='/myapp/login_get')
def add_category_post(request):
    cat_name = request.POST['cat_name']
    Categorys = Category()
    Categorys.cat_name = cat_name
    Categorys.save()
    return redirect('/myapp/add_category_get')


@login_required(login_url='/myapp/login_get')
def update_Product_availabilty_get(request, pro_id):
    Products = Product.objects.get(id=pro_id)
    return render(request, 'Staff/Update Product avilability.html', {'Products': Products})


@login_required(login_url='/myapp/login_get')
def update_Product_availabilty_post(request):
    pro_id = request.POST['pro_id']
    Products = Product.objects.get(id=pro_id)
    Products.status = request.POST['status']
    Products.save()
    return redirect('/myapp/View_product')


@login_required(login_url='/myapp/login_get')
def update_product_quantity(request):
    id = request.POST['id']
    action = request.POST['action']

    product = Product.objects.get(id=id)

    if action == "inc":
        product.Quantity += 1

    if action == "dec" and product.Quantity > 0:
        product.Quantity -= 1

    # 🔥 Automatic Status
    if product.Quantity == 0:
        product.status = "sold Out"
    elif product.Quantity <= 3:
        product.status = "low Stock"
    else:
        product.status = "available"

    product.save()

    return JsonResponse({"status": "ok"})


@login_required(login_url='/myapp/login_get')
def Staff_view_orders(request):
    orders = OderMain.objects.all()
    return render(request, 'Staff/View orders.html', {
        'orders': orders
    })


@login_required(login_url='/myapp/login_get')
def shop_view_order_items(request, oid):
    order = OderMain.objects.get(id=oid)
    items = OderSub.objects.filter(ORDER_MAIN=order)

    return render(request, 'Staff/view_order_items.html', {
        'order': order,
        'items': items
    })

@login_required(login_url='/myapp/login_get')
def view_profile_shop(request):
    staff = Staff.objects.get(AUTHUSER=request.user)
    return render(request, 'Staff/View profile.html', {'data': staff})


@login_required(login_url='/myapp/login_get')
def edit_profile_get(request, shop_id):
    shop = Staff.objects.get(id=shop_id)
    return render(request, 'Staff/Edit shop profile.html', {'shop': shop})


@login_required(login_url='/myapp/login_get')
def edit_profile_shop_post(request):
    shop = Staff.objects.get(id=request.POST['staff_id'])
    shop.name = request.POST['name']
    shop.phone_no = request.POST['phone']
    auth_user = shop.AUTHUSER
    auth_user.username = request.POST['name']
    auth_user.save()
    image = request.FILES['staff_image']
    fs = FileSystemStorage()
    d = datetime.now().strftime("%Y%m%d_%H%M%S")
    shop_filename = d + "_shop.jpg"
    fs.save(shop_filename, image)
    shop.profile = fs.url(shop_filename)
    shop.save()
    return redirect('/myapp/view_profile_shop')


@login_required(login_url='/myapp/login_get')
def view_groomings_get(request):
    grooming_services = GroomingService.objects.all()

    return render(request, 'Staff/View grooming services.html', {
        'data': grooming_services
    })





@login_required(login_url='/myapp/login_get')
def view_grooming_booking(request):
    bookings = GroomingBooking.objects.all()

    return render(request, 'Staff/View grooming services booking.html', {
        'data': bookings
    })


@login_required(login_url='/myapp/login_get')
def update_booking_get(request, gb_id):
    booking = GroomingBooking.objects.get(id=gb_id)
    return render(request, 'Staff/Update booking status.html', {'booking': booking})


@login_required(login_url='/myapp/login_get')
def update_booking_post(request):
    gb_id = request.POST['gb_id']
    booking = GroomingBooking.objects.get(id=gb_id)
    if booking.status == 'accepted':
        booking.status = request.POST['status']
        booking.save()
        return redirect('/myapp/view_grooming_booking')
    else:
        return HttpResponse("Only accepted bookings can be updated.")


@login_required(login_url='/myapp/login_get')
def accepted_booking(request, gb_id):
    booking = GroomingBooking.objects.get(id=gb_id)
    booking.status = 'accepted'
    booking.save()
    return redirect('/myapp/view_grooming_booking')


@login_required(login_url='/myapp/login_get')
def rejected_booking(request, gb_id):
    booking = GroomingBooking.objects.get(id=gb_id)
    booking.status = 'rejected'
    booking.save()
    return redirect('/myapp/view_grooming_booking')


def view_product_get(request):
    pro = Product.objects.all()
    return render(request, 'Staff/View Product.html', {'data': pro})

@login_required(login_url='/myapp/login_get')
def update_order_status_arrow(request, oid, action):

    order = OderMain.objects.get(id=oid)

    status_flow = [
        "paid",
        "order confirmed",
        "packed",
        "dispatched",
        "delivered"
    ]

    # if status not in list, set to first
    if order.status.lower() not in status_flow:
        order.status = status_flow[0]
        order.save()
        return redirect('/myapp/Staff_view_orders/')

    current_index = status_flow.index(order.status.lower())

    if action == "up" and current_index < len(status_flow) - 1:
        order.status = status_flow[current_index + 1]

    elif action == "down" and current_index > 0:
        order.status = status_flow[current_index - 1]

    order.save()

    return redirect('/myapp/Staff_view_orders/')


@login_required(login_url='/myapp/login_get')
def staff_view_complaints(request):
    complaints = Complaints.objects.all().order_by('-id')

    return render(request, 'Staff/view_complaints.html', {
        'complaints': complaints
    })


@login_required(login_url='/myapp/login_get')
def staff_view_reviews(request):
    reviews = Review.objects.all().order_by('-date')

    return render(request, 'Staff/View ratings and review.html', {
        'reviews': reviews
    })

@login_required(login_url='/myapp/login_get')
def staff_view_payments(request):
    orders = OderMain.objects.all().order_by('-id')

    return render(request, 'Staff/view_payment.html', {
        'orders': orders
    })

@login_required(login_url='/myapp/login_get')
def staff_generate_report(request):

    from_date = request.GET.get('from')
    to_date = request.GET.get('to')

    # Only delivered orders
    orders = OderMain.objects.filter(status="delivered")
    bookings = GroomingBooking.objects.filter(status="completed")

    # Date filter (works only if date stored as YYYY-MM-DD string)
    if from_date and to_date:
        orders = orders.filter(date__range=[from_date, to_date])
        bookings = bookings.filter(date__range=[from_date, to_date])

    # Convert total_amount to integer sum safely
    total_sales = 0
    for o in orders:
        total_sales += int(o.total_amount)

    total_orders = orders.count()
    total_grooming = bookings.count()

    return render(request, 'Staff/staff_report.html', {
        'orders': orders,
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_grooming': total_grooming
    })

# USER__________________________________________________________________________________________________________________________________________________________
# @csrf_exempt
# def view_shops(request):
#     l = []
#
#     data = Staff.objects.filter(status='approved')
#
#     for i in data:
#         l.append({
#             'id': i.id,
#             'sname': i.sname,
#             'place': i.place,
#             'post': i.post,
#             'pin': i.pin,
#             'email': i.email,
#             'phone_no': i.phone_no,
#             'owner_name': i.owner_name,
#             'licence_no': i.license_number,
#
#             # ✅ FIX HERE
#             'image': i.shop_image if i.shop_image else "",
#             'owner_profile': i.owner_profile if i.owner_profile else "",
#         })
#
#     return JsonResponse({'status': 'ok', 'data': l})


@csrf_exempt
def view_booking(request):
    lid = request.POST.get('lid')

    if not lid:
        return JsonResponse({
            "status": "error",
            "message": "User id required"
        })

    try:
        cust = customer.objects.get(AUTHUSER_id=lid)
    except customer.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "User not found"
        })

    bookings = GroomingBooking.objects.filter(USER=cust).order_by('-id')

    data = []

    for b in bookings:
        data.append({
            "id": b.id,
            "service_name": b.SERVICE.service_name,
            "pet_name": b.pet_name,
            "pet_type": b.PET_TYPE.pet_type,
            "price": b.SERVICE.price,
            "date": b.date,
            "time": b.time,
            "status": b.status
        })

    return JsonResponse({
        "status": "ok",
        "data": data
    })

def view_groomings(request):

    services = GroomingService.objects.all()

    data = []

    for s in services:
        data.append({
            "id": s.id,
            "service_name": s.service_name,
            "description": s.description,
            "price": s.price,
            "time": s.time,
            "image": str(s.image) if s.image else ""
        })

    return JsonResponse(data, safe=False)


@csrf_exempt
def view_products(request):

    lid = request.POST.get("lid")

    products = Product.objects.all()

    wishlist_ids = []

    if lid:
        try:
            user = customer.objects.get(AUTHUSER_id=lid)
            wishlist_ids = Wishlist.objects.filter(USER=user).values_list('PRODUCT_id', flat=True)
        except:
            pass

    data = []

    for p in products:

        data.append({
            "id": p.id,
            "name": p.pname,
            "brand_name": p.brand_name,
            "Quantity": p.Quantity,
            "description": p.description,
            "price": p.price,
            "image": p.image,
            "is_favorite": p.id in wishlist_ids,
            "seller": "Admin Store"
        })

    return JsonResponse({
        "status": "ok",
        "data": data
    })
@csrf_exempt
def add_cart(request):
    pid = request.POST['pid']
    lid = request.POST['lid']
    qty_str = request.POST['Quantity']  # string

    if not qty_str or int(qty_str) <= 0:
        return JsonResponse({
            'status': 'error',
            'message': 'Quantity must be at least 1'
        })

    quantity = int(qty_str)

    user = User.objects.get(id=lid)
    cust = customer.objects.get(AUTHUSER_id=user)
    product = Product.objects.get(id=pid)

    available_qty = int(product.Quantity)

    if available_qty <= 0:
        return JsonResponse({
            'status': 'error',
            'message': 'Out of stock'
        })

    cart_item = cart.objects.filter(USER=cust, PRODUCT=product).first()

    if cart_item:
        current_qty = int(cart_item.Quantity)
        new_qty = current_qty + quantity

        if new_qty > available_qty:
            return JsonResponse({
                'status': 'error',
                'message': 'Stock Not Available'
            })

        cart_item.Quantity = str(new_qty)
        cart_item.save()

    else:
        if quantity > available_qty:
            return JsonResponse({
                'status': 'error',
                'message': 'Stock Not Available'
            })

        cart.objects.create(
            USER=cust,
            PRODUCT=product,
            Quantity=str(quantity),
            Date=datetime.now().date()
        )

    return JsonResponse({'status': 'ok'})


@csrf_exempt
def update_cart_quantity(request):
    cid = request.POST["cid"]
    action = request.POST["action"]  # inc / dec

    c = cart.objects.get(id=cid)

    # cart quantity (string → int)
    cart_qty = int(c.Quantity)

    # product stock (string → int)
    stock_qty = int(c.PRODUCT.Quantity)

    if action == "inc":
        # 🔒 STOCK LIMIT CHECK
        if cart_qty < stock_qty:
            cart_qty += 1
        else:
            return JsonResponse({
                "status": "error",
                "message": "Out of stock / Stock limit reached"
            })

    elif action == "dec" and cart_qty > 1:
        cart_qty -= 1

    c.Quantity = str(cart_qty)
    c.save()

    return JsonResponse({"status": "ok"})


@csrf_exempt
def view_cart(request):
    lid = request.POST.get('lid')

    if not lid:
        return JsonResponse({"status": "error", "message": "User not found"})

    carts = cart.objects.filter(
        USER__AUTHUSER_id=lid
    ).select_related("PRODUCT__CATEGORY")

    data = []
    total = Decimal(0)

    for c in carts:
        price = Decimal(c.PRODUCT.price)
        qty = int(c.Quantity)
        total += price * qty

        data.append({
            "id": c.id,
            "pname": c.PRODUCT.pname,
            "price": str(price),
            "description": c.PRODUCT.description,
            "Category": c.PRODUCT.CATEGORY.cat_name,
            "Quantity": qty,
            "photo": c.PRODUCT.image
        })

    return JsonResponse({
        "status": "ok",
        "data": data,
        "amount": str(total)
    })


@csrf_exempt
def book_grooming(request):
    lid = request.POST['lid']
    sid = request.POST['sid']
    pet_name = request.POST['pet_name']
    pet_type_id = request.POST['pet_type']  # <-- this must be ID
    date = request.POST['date']
    time = request.POST['time']

    cust = customer.objects.get(AUTHUSER_id=lid)
    service = GroomingService.objects.get(id=sid)
    pet_type = PetType.objects.get(id=pet_type_id)

    address = ShippingAddress.objects.filter(
        USER=cust,
        is_default=True
    ).first()

    if not address:
        return JsonResponse({
            "status": "error",
            "message": "No default address selected"
        })

    b = GroomingBooking()
    b.USER = cust
    b.SERVICE = service
    b.PET_TYPE = pet_type  # ✅ FIXED
    b.ADDRESS = address
    b.pet_name = pet_name
    b.date = date
    b.time = time
    b.status = 'pending'
    b.save()

    return JsonResponse({'status': 'ok'})


# @csrf_exempt
# def view_booking(request):
#     lid = request.POST.get('lid')
#
#     cust = customer.objects.get(AUTHUSER_id=lid)
#
#     bookings = GroomingBooking.objects.filter(USER=cust)
#
#     data = []
#
#     for b in bookings:
#         data.append({
#             "id": b.id,
#             "service_name": b.SERVICE.service_name,
#             "pet_name": b.pet_name,
#             "price": b.SERVICE.price,
#             "pet_type": b.PET_TYPE.pet_type,
#             "date": str(b.date),
#             "time": str(b.time),
#             "status": b.status,
#         })
#
#     return JsonResponse(data, safe=False)


@csrf_exempt
def add_complaint(request):
    lid = request.POST["lid"]
    complaint = request.POST["complaint"]

    user = customer.objects.get(AUTHUSER_id=lid)

    Complaints.objects.create(
        USER=user,
        complaint=complaint,
        date=str(datetime.now().date()),
        status="pending"
    )

    return JsonResponse({"status": "ok"})


@csrf_exempt
def view_complaints(request):
    lid = request.POST["lid"]

    comps = Complaints.objects.filter(
        USER__AUTHUSER__id=lid
    )

    data = []
    for c in comps:
        data.append({
            "id": c.id,
            "complaint": c.complaint,
            "date": c.date,
            "reply": c.reply,
            "status": c.status
        })

    return JsonResponse(data, safe=False)


#
# def buy_product(request):
#     cid = request.POST["cid"]
#     pid = request.POST["pid"]
#
#     user = customer.objects.get(id=cid)
#     product = Product.objects.get(id=pid)
#
#     PetPurchase.objects.create(
#         USER=user,
#         PRODUCT=product,
#         date=datetime.now().strftime("%Y-%m-%d"),
#         payment_status="Paid"
#     )
#
#     return JsonResponse({"status": "ok"})


@csrf_exempt
def user_order_history(request):
    user_id = request.GET.get('user_id')

    # 🔴 1️⃣ VALIDATION
    if not user_id:
        return JsonResponse({
            "status": "error",
            "message": "user_id is required"
        }, status=400)

    if not user_id.isdigit():
        return JsonResponse({
            "status": "error",
            "message": "Invalid user_id"
        }, status=400)

    orders = OderMain.objects.filter(USER_id=int(user_id)).order_by('-id')

    data = []

    for order in orders:

        items = []
        subs = OderSub.objects.filter(ORDER_MAIN=order)

        for o in subs:
            qty = int(o.Quantity)
            price = float(o.unit_price)

            items.append({
                "product": o.PRODUCT.pname,
                "quantity": qty,
                "price": price,
                "total": qty * price,
                "image": str(o.PRODUCT.image) if o.PRODUCT.image else ""
            })

        data.append({
            "order_id": order.id,
            "date": str(order.date),  # ✅ JSON safe
            "status": order.status,
            "total_amount": float(order.total_amount),
            "items": items
        })

    return JsonResponse({
        "status": "ok",
        "data": data
    })

@csrf_exempt
def add_product_review(request):

    lid = request.POST.get("lid")
    pid = request.POST.get("pid")
    rating = request.POST.get("rating")
    review_text = request.POST.get("review")

    if not lid or not pid or not rating or not review_text:
        return JsonResponse({"status": "error", "message": "Missing fields"})

    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            return JsonResponse({"status": "error", "message": "Rating must be 1-5"})
    except:
        return JsonResponse({"status": "error", "message": "Invalid rating"})

    try:
        user = customer.objects.get(AUTHUSER_id=lid)
        product = Product.objects.get(id=pid)
    except:
        return JsonResponse({"status": "error", "message": "Invalid user or product"})

    Review.objects.update_or_create(
        USER=user,
        PRODUCT=product,
        defaults={
            "rating": rating,
            "review": review_text,
            "date": str(datetime.now().date())
        }
    )

    return JsonResponse({"status": "ok"})


def view_reviews(request):
    sid = request.POST["sid"]

    reviews = Review.objects.filter(STAFF=sid)

    data = []
    for r in reviews:
        data.append({
            "rating": r.rating,
            "review": r.review,
            "user": r.USER.cname,
            "date": r.date
        })

    return JsonResponse(data)


#
# @csrf_exempt
# def shop_details(request):
#     lid = request.POST["lid"]
#
#     shop = Staff.objects.get(id=lid, status='approved')
#
#     data = {
#         "id": shop.id,
#         "sname": shop.sname,
#         "email": shop.email,
#         "phone": shop.phone_no,
#         "place": shop.place,
#         "post": shop.post,
#         "pin": shop.pin,
#         "license_number": shop.license_number,
#         "shop_image": shop.shop_image.url if shop.shop_image else "",
#         "owner_name": shop.owner_name,
#         "owner_profile": shop.owner_profile.url if shop.owner_profile else "",
#         "status": shop.status
#     }
#
#     return JsonResponse(data)
#

def search_shops(request):
    query = request.POST["query", ""]

    shops = Staff.objects.filter(sname__icontains=query)

    data = []
    for shop in shops:
        data.append({
            "id": shop.id,
            "sname": shop.sname,
            "place": shop.place,
            "phone": shop.phone_no,
            "email": shop.email
        })

    return JsonResponse(data, safe=False)


# def send_message(request):
#     sender_id = request.POST["sender"]
#     receiver_id = request.POST["receiver"]
#     message = request.POST["message"]
#
#     sender = User.objects.get(id=sender_id)
#     receiver = User.objects.get(id=receiver_id)
#
#     Chat.objects.create(
#         sender=sender,
#         receiver=receiver,
#         message=message
#     )
#
#     return JsonResponse({"status": "ok"})
#
#
# def get_messages(request):
#     sender_id = request.POST["sender"]
#     receiver_id = request.POST["receiver"]
#
#     messages = Chat.objects.filter(
#         sender__in=[sender_id, receiver_id],
#         receiver__in=[sender_id, receiver_id]
#     ).order_by("timestamp")
#
#     data = []
#     for m in messages:
#         data.append({
#             "sender": m.sender.id,
#             "receiver": m.receiver.id,
#             "message": m.message,
#             "time": m.timestamp.strftime("%H:%M"),
#         })
#
#     return JsonResponse(data, safe=False)


@csrf_exempt
def view_profile(request):
    lid = request.POST["lid"]
    user = customer.objects.get(AUTHUSER__id=lid)
    return JsonResponse(
        {"status": "ok", "name": user.cname, "email": user.email, "phone": user.phone_no, "place": user.place,
         "post": user.post, "pin": user.pin, "profile_pic": user.profile_pic.url})


@csrf_exempt
def update_profile(request):
    lid = request.POST["lid"]
    cust = customer.objects.get(AUTHUSER__id=lid)
    new_email = request.POST["email"]
    if User.objects.filter(username=new_email).exclude(id=cust.AUTHUSER.id).exists():
        return JsonResponse({"status": "error", "message": "Email already exists"})
    auth_user = cust.AUTHUSER
    auth_user.username = new_email
    auth_user.email = new_email
    auth_user.save()
    cust.cname = request.POST["cname"]
    cust.email = new_email
    cust.phone_no = request.POST["phone"]
    cust.place = request.POST["place"]
    cust.post = request.POST["post"]
    cust.pin = request.POST["pin"]
    if "image" in request.FILES:
        image = request.FILES["image"]
        fs = FileSystemStorage()
        d = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = d + "_img.jpg"
        fs.save(filename, image)
        cust.profile_pic = filename
    cust.save()
    return JsonResponse({"status": "ok", "message": "Profile updated successfully"})


@csrf_exempt
def filter_shops(request):
    location = request.POST["location"]
    rating = request.POST["rating"]

    shops = Staff.objects.filter(status='approved')

    if location != "":
        shops = shops.filter(place__icontains=location)

    shops = shops.annotate(avg_rating=Avg('review__rating'))

    if rating != "":
        shops = shops.filter(avg_rating__gte=float(rating))

    data = []
    for shop in shops:
        data.append({
            "id": shop.id,
            "name": shop.name,
            "place": shop.place,
            "phone": shop.phone_no,
            "rating": round(shop.avg_rating, 1) if shop.avg_rating else 0
        })

    return JsonResponse({"status": "ok", "data": data})


@csrf_exempt
def user_signuppost(request):
    if request.method != "POST":
        return JsonResponse({"status": "error", "msg": "POST required"})
    name = request.POST["name"]
    email = request.POST["email"]
    phone = request.POST["phone"]
    place = request.POST["place"]
    post = request.POST["post"]
    pin = request.POST["pin"]
    password = request.POST["password"]
    profile_path = ""
    if User.objects.filter(username=email).exists():
        return JsonResponse({
            "status": "error",
            "message": "Email already exists"
        })
    if customer.objects.filter(phone_no=phone).exists():
        return JsonResponse({
            "status": "error",
            "message": "Phone number already registered"
        })
    if "image" in request.FILES:
        image = request.FILES["image"]
        fs = FileSystemStorage()
        d = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_filename = d + "_img.jpg"
        fs.save(image_filename, image)
        profile_path = image_filename

    u = User.objects.create_user(
        username=email,
        password=password
    )
    customer.objects.create(
        AUTHUSER=u,
        cname=name,
        email=email,
        phone_no=phone,
        place=place,
        post=post,
        pin=pin,
        status="active",
        profile_pic=profile_path
    )
    return JsonResponse({"status": "ok", "message": "Account created successfully"})


@csrf_exempt
def deletefromcart(request):
    id = request.POST["cid"]
    cart.objects.get(id=id).delete()

    return JsonResponse(
        {
            'status': 'ok'
        }
    )


@csrf_exempt
def add_address(request):
    lid = request.POST["lid"]

    user = customer.objects.get(AUTHUSER_id=lid)

    ShippingAddress.objects.filter(USER=user, is_default=True).update(is_default=False)

    ShippingAddress.objects.create(
        USER=user,
        name=request.POST["name"],
        house_name=request.POST["house_name"],
        place=request.POST["place"],
        district=request.POST["district"],
        pin=request.POST["pin"],
        landmark=request.POST.get("landmark", ""),
        phone=request.POST["phone"],
        is_default=True
    )

    return JsonResponse({"status": "ok"})


@csrf_exempt
def get_addresses(request):
    lid = request.POST["lid"]

    addresses = ShippingAddress.objects.filter(USER__AUTHUSER_id=lid)

    data = []
    for a in addresses:
        data.append({
            "id": a.id,
            "name": a.name,
            "house_name": a.house_name,
            "place": a.place,
            "district": a.district,
            "pin": a.pin,
            "phone": a.phone,
            "is_default": a.is_default
        })

    return JsonResponse({"status": "ok", "data": data})


@csrf_exempt
def set_default_address(request):
    lid = request.POST["lid"]
    address_id = request.POST["address_id"]

    user = customer.objects.get(AUTHUSER_id=lid)

    ShippingAddress.objects.filter(USER=user).update(is_default=False)

    ShippingAddress.objects.filter(id=address_id).update(is_default=True)

    return JsonResponse({"status": "ok"})


def view_pet_types(request):
    if request.method == "GET":
        data = PetType.objects.all().values('id', 'pet_type')

        return JsonResponse(list(data), safe=False)

    return JsonResponse({'status': 'invalid'})

from django.db import transaction

@csrf_exempt
def cartpayment(request):

    lid = request.POST.get('lid')
    amount = request.POST.get('amount')

    if not lid or not amount:
        return JsonResponse({
            "status": "error",
            "message": "Invalid data"
        })

    try:
        user = customer.objects.get(AUTHUSER_id=lid)
    except customer.DoesNotExist:
        return JsonResponse({
            "status": "error",
            "message": "User not found"
        })

    cart_items = cart.objects.filter(USER=user)

    if not cart_items.exists():
        return JsonResponse({"status": "empty"})

    # ✅ Get default address
    address = ShippingAddress.objects.filter(
        USER=user,
        is_default=True
    ).first()

    if not address:
        return JsonResponse({
            "status": "error",
            "message": "No default address selected"
        })

    # 🔥 Use transaction to prevent partial order creation
    with transaction.atomic():

        # ✅ Check stock FIRST
        for c in cart_items:
            if c.PRODUCT.Quantity < int(c.Quantity):
                return JsonResponse({
                    "status": "error",
                    "message": f"{c.PRODUCT.pname} stock not available"
                })

        # ✅ Create OrderMain AFTER stock check
        order = OderMain.objects.create(
            USER=user,
            ADDRESS=address,
            total_amount=amount,
            status="paid",
            date=str(timezone.now().date())
        )

        # ✅ Create OrderSub & Reduce Stock
        for c in cart_items:

            OderSub.objects.create(
                ORDER_MAIN=order,
                PRODUCT=c.PRODUCT,
                Quantity=c.Quantity,
                unit_price=c.PRODUCT.price
            )

            # Reduce stock
            c.PRODUCT.Quantity -= int(c.Quantity)
            c.PRODUCT.save()

        # Clear cart
        cart_items.delete()

    return JsonResponse({
        "status": "ok",
        "message": "Order placed successfully"
    })


@csrf_exempt
def view_staff(request):
    staff_list = Staff.objects.filter(status='approved')

    data = []

    for i in staff_list:
        data.append({
            "id": i.id,
            "name": i.name,
            "profile": i.profile,
            "phone_no": i.phone_no,
            "status": i.status,
        })

    return JsonResponse({
        "status": "ok",
        "data": data
    })


@csrf_exempt
def filter_groomers(request):
    place = request.POST["place"]
    rating = request.POST["rating"]
    price = request.POST["price"]

    shops = Staff.objects.filter(status='approved')

    if place != "":
        shops = shops.filter(place__icontains=place)

    shops = shops.annotate(avg_rating=Avg('review__rating'))

    if rating != "":
        shops = shops.filter(avg_rating__gte=float(rating))

    shops = shops.annotate(min_price=Min(Cast('groomingservice__price', FloatField())))

    if price != "":
        shops = shops.filter(min_price__lte=float(price))

    data = []
    for s in shops:
        data.append({
            "id": s.id,
            "name": s.name,
            "place": s.place,
            "profile": s.profile,
            "rating": round(s.avg_rating, 1) if s.avg_rating else 0,
            "starting_price": s.min_price if s.min_price else 0
        })

    return JsonResponse({"status": "ok", "data": data})


@csrf_exempt
def view_pet_types(request):
    data = PetType.objects.all().values('id', 'pet_type')
    return JsonResponse({
        "status": "ok",
        "data": list(data)
    })


@csrf_exempt
def change_password(request):
    current_password = request.POST['current_password']
    new_password = request.POST['new_password']
    lid = request.POST['lid']
    try:
        user = User.objects.get(id=lid)
        if not user.check_password(current_password):
            return JsonResponse({'status': 'error', 'message': 'Current password incorrect'})
        user.set_password(new_password)
        user.save()
        return JsonResponse({'status': 'ok', 'message': 'Password changed successfully'})
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'User not found'})


@csrf_exempt
def logout_user(request):
    return JsonResponse({"status": "ok", "message": "Logged out successfully"})


@csrf_exempt
def toggle_wishlist(request):

    lid = request.POST.get("lid")
    pid = request.POST.get("pid")

    try:
        user = customer.objects.get(AUTHUSER_id=lid)
        product = Product.objects.get(id=pid)
    except:
        return JsonResponse({"status": "error"})

    wishlist_item = Wishlist.objects.filter(USER=user, PRODUCT=product)

    if wishlist_item.exists():
        wishlist_item.delete()
        return JsonResponse({"status": "removed"})
    else:
        Wishlist.objects.create(USER=user, PRODUCT=product)
        return JsonResponse({"status": "added"})


@csrf_exempt
def view_wishlist(request):

    lid = request.POST.get("lid")

    try:
        user = customer.objects.get(AUTHUSER_id=lid)
    except:
        return JsonResponse({"status": "error"})

    items = Wishlist.objects.filter(USER=user)

    data = []

    for w in items:
        p = w.PRODUCT
        data.append({
            "id": p.id,
            "name": p.pname,
            "price": p.price,
            "Quantity": p.Quantity,
            "image": p.image,
            "seller": "Admin Store"
        })

    return JsonResponse({
        "status": "ok",
        "data": data
    })

# public

from django.http import JsonResponse

from django.http import JsonResponse

from django.http import JsonResponse

def public_home(request):

    products = Product.objects.all()
    services = GroomingService.objects.all()

    product_data = []
    for p in products:
        product_data.append({
            "id": p.id,
            "name": p.pname,
            "price": p.price,
            "image": p.image   # ✅ CharField (no .url)
        })

    service_data = []
    for s in services:
        service_data.append({
            "id": s.id,
            "name": s.service_name,
            "price": s.price,
            "image": str(s.image) if s.image else ""
        })

    return JsonResponse({
        "products": product_data,
        "services": service_data
    })
@csrf_exempt
def public_view_products(request):

    products = Product.objects.all()

    data = []
    for p in products:
        data.append({
            "id": p.id,
            "name": p.pname,
            "brand_name": p.brand_name,
            "price": p.price,
            "image": p.image,
            "description": p.description
        })

    return JsonResponse({
        "status": "ok",
        "data": data
    })


@csrf_exempt
def public_view_groomings(request):

    services = GroomingService.objects.all()

    data = []
    for s in services:
        data.append({
            "id": s.id,
            "service_name": s.service_name,
            "price": s.price,
            "time": s.time,
            "image": s.image
        })

    return JsonResponse({
        "status": "ok",
        "data": data
    })

@csrf_exempt
def public_view_groomings(request):

    services = GroomingService.objects.all()

    data = []
    for s in services:
        data.append({
            "id": s.id,
            "service_name": s.service_name,
            "price": s.price,
            "time": s.time,
            "image": s.image
        })

    return JsonResponse({
        "status": "ok",
        "data": data
    })


@csrf_exempt
def public_view_reviews(request):

    reviews = Review.objects.all().order_by('-date')

    data = []
    for r in reviews:
        data.append({
            "product": r.PRODUCT.pname,
            "rating": r.rating,
            "review": r.review,
            "date": r.date
        })

    return JsonResponse({
        "status": "ok",
        "data": data
    })


@csrf_exempt
def add_cart(request):

    lid = request.POST.get("lid")

    if not lid:
        return JsonResponse({
            "status": "login_required",
            "message": "Please login first"
        })

    pid = request.POST.get("pid")
    qty = request.POST.get("Quantity")

    if not pid or not qty:
        return JsonResponse({"status": "error"})

    user = customer.objects.get(AUTHUSER_id=lid)
    product = Product.objects.get(id=pid)

    cart.objects.create(
        USER=user,
        PRODUCT=product,
        Quantity=qty,
        Date=datetime.now().date()
    )

    return JsonResponse({"status": "ok"})


@csrf_exempt
def book_grooming(request):

    lid = request.POST.get("lid")

    if not lid:
        return JsonResponse({
            "status": "login_required"
        })


@csrf_exempt
def toggle_wishlist(request):

    lid = request.POST.get("lid")

    if not lid:
        return JsonResponse({
            "status": "login_required"
        })

