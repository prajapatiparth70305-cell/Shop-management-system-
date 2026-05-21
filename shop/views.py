from django.utils import timezone

from django.shortcuts import render, redirect

from .models import Attendance, BillItem, Expense, Product,Customer,Bill,Category,Employee, Supplier, UserProfile
from django.db.models import Sum, Count
from datetime import date
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from datetime import datetime
from datetime import timedelta
from django.utils import timezone
from django.db.models.functions import TruncDate
import json
cart = {}

def signup_page(request):

    error = ""

    if request.method == "POST":

        username = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        role = request.POST.get(
            'role'
        )

        # CHECK USER EXISTS

        if User.objects.filter(
            username=username
        ).exists():

            error = "Username Already Exists"

        else:

            # CREATE USER

            user = User.objects.create_user(

                username=username,

                password=password

            )

            # CREATE USER PROFILE

            UserProfile.objects.create(

                user=user,

                role=role

            )

            return redirect('/login/')

    context = {

        'error': error

    }

    return render(
        request,
        'signup.html',
        context
    )

def login_page(request):

    error = ""

    if request.method == "POST":

        username = request.POST.get(
            'username'
        )

        password = request.POST.get(
            'password'
        )

        user = authenticate(

            username=username,

            password=password

        )

        if user is not None:

            login(request, user)

            return redirect('/dashboard/')

        else:

            error = "Invalid Username or Password"

    context = {

        'error': error

    }

    return render(
        request,
        'login.html',
        context
    )

def logout_page(request):

    logout(request)

    return redirect('/login/')

@login_required
def dashboard(request):

    # TOTAL PRODUCTS

    products = Product.objects.count()

    # TOTAL EMPLOYEES

    employees = Employee.objects.count()

    # TOTAL BILLS

    valid_bills = Bill.objects.annotate(
        item_count=Count('billitem')
    ).filter(
        item_count__gt=0
    )

    bills = valid_bills.count()

    # TOTAL SUPPLIERS

    suppliers = Supplier.objects.count()

    # TOTAL SALES

    total_sales = valid_bills.aggregate(
        Sum('total_amount')
    )['total_amount__sum'] or 0

    # TOTAL EXPENSES

    total_expense = 0

    all_expenses = Expense.objects.all()

    for expense in all_expenses:

        total_expense += expense.amount

    # USER ROLE

    role = request.user.userprofile.role

    context = {

        'products': products,

        'employees': employees,

        'bills': bills,

        'suppliers': suppliers,

        'total_sales': total_sales,

        'total_expense': total_expense,

        'role': role

    }

    return render(
        request,
        'dashboard.html',
        context
    )


def products(request):

    if request.method == "POST":
        category_id = request.POST.get('category')
        name = request.POST.get('name')
        barcode = request.POST.get('barcode')
        price = request.POST.get('price')
        quantity = request.POST.get('quantity')

        category = Category.objects.get(id=category_id)

        Product.objects.create(
            category=category,
            name=name,
            barcode=barcode,
            price=price,
            quantity=quantity
        )

        return redirect('/products/')

    products = Product.objects.all()
    categories = Category.objects.all()

    context = {
        'products': products,
        'categories': categories
    }

    return render(request, 'products.html', context)


def delete_product(request, id):
    product = Product.objects.filter(id=id).first()
    if product:
        product.delete()
        Bill.objects.filter(billitem__isnull=True).delete()
    return redirect('/products/')

def billing(request):

    search = request.GET.get('search')

    if search:
        products = Product.objects.filter(name__icontains=search)
    else:
        products = Product.objects.all()

    total = 0
    cart_items = []

    for key, item in cart.items():
        subtotal = item['subtotal']
        total += subtotal

        product = Product.objects.filter(id=item['id']).first()

        gst_percent = product.gst if product and product.gst else 0
        gst_amount = subtotal * gst_percent / 100

        cart_items.append({
            **item,
            'gst_percent': gst_percent,
            'gst_amount': round(gst_amount, 2),
            'final_amount': round(subtotal + gst_amount, 2)
        })

    cgst = round(total * 0.09, 2)
    sgst = round(total * 0.09, 2)
    final_amount = round(total + cgst + sgst, 2)

    context = {
        'products': products,
        'cart': cart_items,
        'total': round(total, 2),
        'cgst': cgst,
        'sgst': sgst,
        'final_amount': final_amount
    }

    return render(request, 'billing.html', context)


def add_to_cart(request, id):

    product = Product.objects.get(id=id)

    # CHECK STOCK
    if product.stock <= 0:
        return redirect('/billing/')

    if str(id) in cart:

        # STOCK LIMIT CHECK
        if cart[str(id)]['quantity'] < product.stock:
            cart[str(id)]['quantity'] += 1
            cart[str(id)]['subtotal'] = (
                cart[str(id)]['price'] *
                cart[str(id)]['quantity']
            )

    else:
        cart[str(id)] = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'quantity': 1,
            'subtotal': product.price
        }

    return redirect('/billing/')


def save_bill(request):

    cart_items = list(cart.values())

    if not cart_items:
        return redirect('/billing/')

    subtotal = 0

    for item in cart_items:
        subtotal += item['subtotal']

    # GST
    cgst = subtotal * 0.09
    sgst = subtotal * 0.09
    final_total = subtotal + cgst + sgst

    # SAVE BILL
    bill = Bill.objects.create(
        total_amount=subtotal,
        cgst=cgst,
        sgst=sgst,
        final_amount=final_total
    )

    for item in cart_items:

        product = Product.objects.get(id=item['id'])

        # REDUCE STOCK
        if product.quantity is None:
            product.quantity = 0
        else:
            product.quantity = max(product.quantity - item['quantity'], 0)
        product.save()

        # SAVE BILL ITEMS
        BillItem.objects.create(
            bill=bill,
            product=product,
            quantity=item['quantity'],
            price=item['subtotal']
        )

    # CLEAR CART
    cart.clear()

    return redirect(f'/receipt/{bill.id}/')

def barcode_scan(request):

    if request.method == "POST":

        barcode = request.POST.get('barcode')

        try:
            product = Product.objects.get(barcode=barcode)

            product_id = str(product.id)

            if product_id in cart:

                cart[product_id]['quantity'] += 1
                cart[product_id]['subtotal'] += product.price

            else:

                cart[product_id] = {
                    'id': product.id,
                    'name': product.name,
                    'price': product.price,
                    'quantity': 1,
                    'subtotal': product.price
                }

        except:
            pass

    return redirect('/billing/')


def reports(request):

    today = date.today()

    # Today's bills
    bills = Bill.objects.filter(created_at__date=today)

    # Total Sales
    total_sales = bills.aggregate(
        Sum('total_amount')
    )

    # Total Bills Count
    total_bills = bills.count()

    # Sold Products
    items = BillItem.objects.filter(
        bill__created_at__date=today
    )

    context = {
        'bills': bills,
        'total_sales': total_sales,
        'total_bills': total_bills,
        'items': items
    }

    return render(request, 'reports.html', context)



def profit_dashboard(request):

    # DELETE 30 DAYS OLD BILLS

    one_month_ago = timezone.now() - timedelta(days=30)

    Bill.objects.filter(
        created_at__lt=one_month_ago
    ).delete()

    # PROFIT CALCULATION

    items = BillItem.objects.all()

    total_profit = 0

    total_sales = 0

    for item in items:

        selling = item.price

        purchase_price = (
            item.product.purchase_price or 0
        )

        purchase = (
            purchase_price * item.quantity
        )

        profit = selling - purchase

        total_profit += profit

        total_sales += selling

    context = {

        'profit': total_profit,

        'total_sales': total_sales

    }

    return render(

        request,

        'profit.html',

        context
    )
def receipt(request, id):

    bill = Bill.objects.get(id=id)

    items = BillItem.objects.filter(bill=bill)

    context = {
        'bill': bill,
        'items': items
    }

    return render(request, 'receipt.html', context)

def employees(request):

    if request.method == "POST":

        name = request.POST.get('name')

        mobile = request.POST.get('phone') or request.POST.get('mobile')

        address = request.POST.get(
            'address'
        )

        position = request.POST.get(
            'position'
        )

        salary = request.POST.get(
            'salary'
        )

        # SAVE EMPLOYEE
        # Parse salary to float, default to 0 on invalid input
        try:
            salary_val = float(salary) if salary not in (None, '') else 0.0
        except (TypeError, ValueError):
            salary_val = 0.0

        # Parse optional joining_date from form (expected YYYY-MM-DD)
        joining_date_str = request.POST.get('joining_date')
        if joining_date_str:
            try:
                joining_date_val = date.fromisoformat(joining_date_str)
            except Exception:
                joining_date_val = None
        else:
            joining_date_val = None

        Employee.objects.create(
            name=name,
            mobile=mobile,
            address=address,
            position=position,
            salary=salary_val,
            joining_date=joining_date_val
        )

        # AUTO EXPENSE ENTRY
        Expense.objects.create(
            title=f"Salary - {name}",
            amount=salary_val
        )

    employees = Employee.objects.all()

    total_salary = 0.0

    for emp in employees:

        total_salary += (emp.salary or 0)

    context = {

        'employees': employees,

        'total_salary': total_salary

    }

    return render(
        request,
        'employees.html',
        context
    )


def delete_employee(request, id):

    employee = Employee.objects.get(
        id=id
    )

    employee.delete()

    return redirect('/employees/')

def profit_reports(request):

    today = timezone.now().date()

    # DAILY PROFIT

    daily_items = BillItem.objects.filter(
        bill__created_at__date=today
    )

    daily_profit = 0

    for item in daily_items:

        selling = item.price

        purchase = (
            (item.product.purchase_price or 0) *
            item.quantity
        )

        daily_profit += (selling - purchase)

    # MONTHLY PROFIT

    current_month = today.month
    current_year = today.year

    monthly_items = BillItem.objects.filter(
        bill__created_at__month=current_month,
        bill__created_at__year=current_year
    )

    monthly_profit = 0

    for item in monthly_items:

        selling = item.price

        purchase = (
            (item.product.purchase_price or 0) *
            item.quantity
        )

        monthly_profit += (selling - purchase)

    # YEARLY PROFIT

    yearly_items = BillItem.objects.filter(
        bill__created_at__year=current_year
    )

    yearly_profit = 0

    for item in yearly_items:

        selling = item.price

        purchase = (
            (item.product.purchase_price or 0) *
            item.quantity
        )

        yearly_profit += (selling - purchase)

    context = {

        'daily_profit': daily_profit,

        'monthly_profit': monthly_profit,

        'yearly_profit': yearly_profit,

    }

    return render(
        request,
        'profit_reports.html',
        context
    )

from django.utils import timezone

def expenses(request):

    if request.method == "POST":

        title = request.POST.get('title')

        amount = request.POST.get('amount')

        Expense.objects.create(
            title=title,
            amount=amount
        )

    expenses = Expense.objects.all()

    today = timezone.now().date()

    current_month = today.month

    current_year = today.year

    # Daily Expense

    daily_expenses = Expense.objects.filter(
        created_at__date=today
    )

    daily_total = 0

    for expense in daily_expenses:

        daily_total += expense.amount

    # Monthly Expense

    monthly_expenses = Expense.objects.filter(
        created_at__month=current_month,
        created_at__year=current_year
    )

    monthly_total = 0

    for expense in monthly_expenses:

        monthly_total += expense.amount

    # Yearly Expense

    yearly_expenses = Expense.objects.filter(
        created_at__year=current_year
    )

    yearly_total = 0

    for expense in yearly_expenses:

        yearly_total += expense.amount

    context = {

        'expenses': expenses,

        'daily_total': daily_total,

        'monthly_total': monthly_total,

        'yearly_total': yearly_total

    }

    return render(
        request,
        'expenses.html',
        context
    )

def delete_expense(request, id):

    expense = Expense.objects.get(id=id)

    expense.delete()

    return redirect('/expenses/')

def stock_alert(request):

    products = Product.objects.all()

    low_stock_products = []

    out_of_stock_products = []

    for product in products:

        # LOW STOCK: only compare when both values are present
        if (
            product.quantity is not None
            and product.low_stock_alert is not None
            and product.quantity <= product.low_stock_alert
            and product.quantity > 0
        ):
            low_stock_products.append(product)

        # OUT OF STOCK

        if product.quantity == 0:

            out_of_stock_products.append(
                product
            )

    context = {

        'low_stock_products':
        low_stock_products,

        'out_of_stock_products':
        out_of_stock_products

    }

    return render(
        request,
        'stock_alert.html',
        context
    )

def suppliers(request):

    if request.method == "POST":

        name = request.POST.get(
            'name'
        )

        phone = request.POST.get(
            'phone'
        )

        email = request.POST.get(
            'email'
        )

        address = request.POST.get(
            'address'
        )

        company = request.POST.get(
            'company'
        )

        Supplier.objects.create(

            name=name,

            phone=phone,

            email=email,

            address=address,

            company=company

        )

    suppliers = Supplier.objects.all()

    context = {

        'suppliers': suppliers

    }

    return render(
        request,
        'suppliers.html',
        context
    )


def delete_supplier(request, id):

    supplier = Supplier.objects.get(
        id=id
    )

    supplier.delete()

    return redirect('/suppliers/')



def attendance(request):

    employees = Employee.objects.all()

    records = Attendance.objects.all().order_by(
        '-id'
    )

    if request.method == "POST":

        employee_id = request.POST.get(
            'employee'
        )

        action = request.POST.get(
            'action'
        )

        employee = Employee.objects.get(
            id=employee_id
        )

        today = Attendance.objects.filter(
            employee=employee,
            date=datetime.today().date()
        ).first()

        # CHECK IN

        if action == "checkin":

            if not today:

                Attendance.objects.create(

                    employee=employee,

                    check_in=datetime.now().time(),

                    status='Present'

                )

        # CHECK OUT

        if action == "checkout":

            if today:

                today.check_out = datetime.now().time()

                today.save()

        return redirect(
            'attendance'
        )

    context = {

        'employees': employees,

        'records': records

    }

    return render(

        request,

        'attendance.html',

        context
    )

def delete_attendance(request, id):

    record = Attendance.objects.get(
        id=id
    )

    record.delete()

    return redirect('/attendance/')

def analytics_dashboard(request):

    # DAILY SALES

    sales = Bill.objects.annotate(

        day=TruncDate('created_at')

    ).values('day').annotate(

        total=Sum('total_amount')

    ).order_by('day')

    sales_labels = []

    sales_data = []

    for sale in sales:

        sales_labels.append(

            sale['day'].strftime("%d %b")

        )

        sales_data.append(

            float(sale['total'])

        )

    # TOTAL PROFIT

    items = BillItem.objects.all()

    total_profit = 0

    for item in items:

        selling = item.price

        purchase_price = item.product.purchase_price or 0
        purchase = purchase_price * (item.quantity or 0)

        profit = selling - purchase

        total_profit += profit

    # TOTAL EXPENSE

    total_expense = Expense.objects.aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    context = {

        'sales_labels': json.dumps(
            sales_labels
        ),

        'sales_data': json.dumps(
            sales_data
        ),

        'profit': total_profit,

        'expense': total_expense

    }

    return render(

        request,

        'analytics.html',

        context
    )

