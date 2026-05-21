from django.contrib import admin
from .models import UserProfile,Product, Bill, BillItem,Category,Customer,Employee,Expense,Supplier

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Product)
admin.site.register(Bill)
admin.site.register(BillItem)
admin.site.register(Employee)
admin.site.register(Expense)
admin.site.register(Category)
admin.site.register(Customer)
admin.site.register(Supplier)
