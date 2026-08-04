from django.db import models
from django.contrib.auth.models import User


# class petshop(models.Model):
#     AUTHUSER = models.OneToOneField(User, on_delete=models.CASCADE)
#     sname = models.CharField(max_length=100)
#     email = models.EmailField(max_length=100)
#     phone_no = models.CharField(max_length=100)
#     place = models.CharField(max_length=100)
#     post = models.CharField(max_length=100)
#     pin = models.CharField(max_length=100)
#     license_number = models.CharField(max_length=100)
#     shop_image = models.CharField(max_length=500)
#     owner_name = models.CharField(max_length=100)
#     owner_profile = models.CharField(max_length=100)
#     status = models.CharField(max_length=100, default='pending')


class customer(models.Model):
    AUTHUSER = models.OneToOneField(User, on_delete=models.CASCADE)
    cname = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    phone_no = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    post = models.CharField(max_length=100)
    pin = models.CharField(max_length=100)
    profile_pic = models.ImageField()
    status = models.CharField(max_length=100, default='active')


class Staff(models.Model):
    AUTHUSER = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    place=models.CharField(max_length=700)
    pin=models.CharField(max_length=200)
    post=models.CharField(max_length=200)
    profile = models.CharField(max_length=500)
    phone_no = models.CharField(max_length=15)
    status = models.CharField(max_length=20, default='pending')

class ShippingAddress(models.Model):
    USER = models.ForeignKey(customer, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    house_name = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    pin = models.CharField(max_length=10)
    landmark = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15)
    is_default = models.BooleanField(default=False)


class GroomingService(models.Model):
    # SHOP = models.ForeignKey(petshop, on_delete=models.CASCADE)
    service_name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.CharField(max_length=100)
    image = models.ImageField()
    time = models.CharField(max_length=100)


class PetType(models.Model):
    pet_type = models.CharField(max_length=50)


class GroomingBooking(models.Model):
    USER = models.ForeignKey(customer, on_delete=models.CASCADE)
    SERVICE = models.ForeignKey(GroomingService, on_delete=models.CASCADE)
    ADDRESS = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE)
    pet_name = models.CharField(max_length=100)
    PET_TYPE = models.ForeignKey(PetType, on_delete=models.CASCADE)
    # pet_type = models.CharField(max_length=100)
    date = models.CharField(max_length=100)
    time = models.CharField(max_length=100)
    status = models.CharField(max_length=100, default='pending')


class Category(models.Model):
    cat_name = models.CharField(max_length=100)


class Product(models.Model):
    CATEGORY = models.ForeignKey(Category, on_delete=models.CASCADE)
    # SHOP = models.ForeignKey(petshop, on_delete=models.CASCADE)
    pname = models.CharField(max_length=100)
    brand_name = models.CharField(max_length=100)
    # Category = models.CharField(max_length=100)
    Quantity = models.IntegerField()
    description = models.TextField()
    price = models.CharField(max_length=100)
    image = models.CharField(max_length=500)
    status = models.CharField(max_length=50)


class cart(models.Model):
    USER = models.ForeignKey(customer, on_delete=models.CASCADE)
    PRODUCT = models.ForeignKey(Product, on_delete=models.CASCADE)
    Quantity = models.CharField(max_length=1000)
    Date = models.DateTimeField(auto_now_add=True)


# class PetPurchase(models.Model):
#     USER = models.ForeignKey(customer, on_delete=models.CASCADE)
#     PRODUCT = models.ForeignKey(Product, on_delete=models.CASCADE)
#     date = models.CharField(max_length=100)
#     payment_status = models.CharField(max_length=100)
#     amount = models.CharField(max_length=1000)


class Wishlist(models.Model):
    USER = models.ForeignKey(customer, on_delete=models.CASCADE)
    PRODUCT = models.ForeignKey(Product, on_delete=models.CASCADE)


class OderMain(models.Model):
    date = models.CharField(max_length=100)
    USER = models.ForeignKey(customer, on_delete=models.CASCADE)
    total_amount = models.CharField(max_length=100)
    status = models.CharField(max_length=100)
    ADDRESS = models.ForeignKey(ShippingAddress, on_delete=models.CASCADE)
    # SHOP = models.ForeignKey(petshop, on_delete=models.CASCADE)


class OderSub(models.Model):
    ORDER_MAIN = models.ForeignKey(OderMain, on_delete=models.CASCADE)
    PRODUCT = models.ForeignKey(Product, on_delete=models.CASCADE)
    Quantity = models.CharField(max_length=100)
    unit_price = models.CharField(max_length=100)


class Review(models.Model):
    USER = models.ForeignKey(customer, on_delete=models.CASCADE)
    PRODUCT = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review = models.TextField()
    date = models.CharField(max_length=100)

class Complaints(models.Model):
    complaint = models.CharField(max_length=500)
    USER = models.ForeignKey(customer, on_delete=models.CASCADE)
    date = models.CharField(max_length=100)
    status = models.CharField(max_length=100, default='pending')
    reply = models.CharField(max_length=500)
