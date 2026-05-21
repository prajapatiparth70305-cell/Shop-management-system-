from django.db import models

from django.contrib.auth.models import User

class UserProfile(models.Model):

    ROLE_CHOICES = (

        ('owner', 'Owner'),

        ('cashier', 'Cashier')

    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    def __str__(self):

        return self.user.username

class Product(models.Model):
    category=models.CharField(max_length=100,null=True, blank=True)
    name=models.CharField(max_length=100,null=True, blank=True)
    barcode=models.CharField(max_length=100, null=True, blank=True)
    price=models.FloatField(null=True, blank=True)
    quantity=models.IntegerField(null=True, blank=True)
    low_stock_alert=models.IntegerField(null=True, blank=True)
    gst=models.FloatField(default=0, null=True, blank=True)
    purchase_price=models.FloatField(null=True, blank=True)
    stock = models.IntegerField(null=True, blank=True)
    

    def __str__(self):
        return self.name
    
class Customer(models.Model):
    name = models.CharField(max_length=100,null=True, blank=True)
    mobile = models.CharField(max_length=15,null=True, blank=True)

    def __str__(self):
        return self.name


class Bill(models.Model):
    customer=models.ForeignKey('Customer', on_delete=models.CASCADE,null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True,null=True, blank=True )
    total_amount=models.FloatField(default=0,null=True, blank=True)
    cgst=models.FloatField(default=0,null=True, blank=True)
    sgst=models.FloatField(default=0,null=True, blank=True)
    final_amount=models.FloatField(default=0,null=True, blank=True)
    created_at=models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __str__(self):
        return str(self.id)

class BillItem(models.Model):
    bill=models.ForeignKey(Bill,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    quantity=models.FloatField(null=True, blank=True)
    price=models.FloatField(null=True, blank=True)

class Category(models.Model):
    name = models.CharField(max_length=100,null=True, blank=True)

    def __str__(self):
        return self.name

class Employee(models.Model):
    name = models.CharField(max_length=100,null=True, blank=True)
    mobile = models.CharField(max_length=15,null=True, blank=True)
    position = models.CharField(max_length=100,null=True, blank=True)
    salary = models.FloatField(null=True, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    
class Expense(models.Model):

    title = models.CharField(max_length=200)

    amount = models.FloatField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title
    
class Supplier(models.Model):

    name = models.CharField(
        max_length=200
    )

    phone = models.CharField(
        max_length=20
    )

    email = models.EmailField()

    address = models.TextField()

    company = models.CharField(
        max_length=200
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):

        return self.name
    
class Attendance(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE
    )

    date = models.DateField(
        auto_now_add=True
    )

    check_in = models.TimeField(
        null=True,
        blank=True
    )

    check_out = models.TimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        default='Present'
    )

    def __str__(self):

        return self.employee.name