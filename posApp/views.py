from pickle import FALSE
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.http import JsonResponse
from posApp.models import Category, CategoryType, Products, Sales, salesItems, Supplier, Purchases, purchaseItems, WarrantyClaim
from django.db.models import Count, Sum, F
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
import json, sys, calendar
from datetime import date, datetime, timedelta
from django.utils import timezone

# ==========================================
# SATPAM PENGECEK HAK AKSES (HANYA BOS)
# ==========================================
def is_admin(user):
    return user.is_superuser

# Login
def login_user(request):
    logout(request)
    resp = {"status":'failed','msg':''}
    username = ''
    password = ''
    if request.POST:
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                resp['status']='success'
            else:
                resp['msg'] = "Incorrect username or password"
        else:
            resp['msg'] = "Incorrect username or password"
    return HttpResponse(json.dumps(resp),content_type='application/json')

#Logout
def logoutuser(request):
    logout(request)
    return redirect('/')

# Create your views here.
@login_required
def home(request):
    from django.utils import timezone
    date_param = request.GET.get('date')
    if date_param:
        try:
            if len(date_param) > 10:
                now_unaware = datetime.strptime(date_param, "%Y-%m-%d %H:%M")
            else:
                now_unaware = datetime.strptime(date_param, "%Y-%m-%d")
            now = timezone.make_aware(now_unaware)
        except ValueError:
            now = timezone.localtime(timezone.now())
    else:
        now = timezone.localtime(timezone.now())

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    yesterday_start = today_start - timedelta(days=1)
    
    current_year = now.strftime("%Y")
    current_month = now.strftime("%m")
    current_day = now.strftime("%d")
    
    # 1. Statistik Dasar
    categories = Category.objects.all().count() 
    products = Products.objects.all().count()   
    
    month_start = today_start.replace(day=1)
    if month_start.month == 12:
        next_month_start = month_start.replace(year=month_start.year+1, month=1)
    else:
        next_month_start = month_start.replace(month=month_start.month+1)
        
    last_month_start = (month_start - timedelta(days=1)).replace(day=1)
    
    # =======================================================
    # 2. LOGIKA GRAFIK SAHAM DINAMIS & STATISTIK KARTU
    # =======================================================
    if request.user.is_superuser:
        base_sales_qs = Sales.objects.all()
    else:
        base_sales_qs = Sales.objects.filter(cashier=request.user)

    filter_chart = request.GET.get('filter_chart', 'bulan_ini')
    sales_dates = []
    sales_amounts = []
    chart_title = ""
    selected_period_name = ""
    transaction = 0

    if filter_chart == 'hari_ini':
        selected_period_name = f"Hari Ini ({now.strftime('%d %b %Y')})"
        chart_title = f"Periode Hari Ini ({now.strftime('%d %b %Y')})"
        sales_today_list = list(base_sales_qs.filter(date_added__gte=today_start, date_added__lt=today_end))
        transaction = len(sales_today_list)
        
        for h in range(0, 24):
            hourly_revenue = sum(s.grand_total for s in sales_today_list if timezone.localtime(s.date_added).hour == h)
            sales_dates.append(f"{h:02d}:00")
            sales_amounts.append(float(hourly_revenue))
            
        chart_total_val = sum(sales_amounts)
        
        yesterday_total_agg = base_sales_qs.filter(date_added__gte=yesterday_start, date_added__lt=today_start).aggregate(Sum('grand_total'))['grand_total__sum']
        yesterday_total = float(yesterday_total_agg) if yesterday_total_agg else 0.0
        
        if yesterday_total > 0:
            chart_pct = ((chart_total_val - yesterday_total) / yesterday_total) * 100
        else:
            chart_pct = 100.0 if chart_total_val > 0 else 0.0

    elif filter_chart == 'minggu_ini':
        start_of_week = today_start - timedelta(days=today_start.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        
        selected_period_name = f"Minggu Ini ({start_of_week.strftime('%d %b')} - {(end_of_week - timedelta(days=1)).strftime('%d %b %Y')})"
        chart_title = f"Periode {selected_period_name}"
        
        sales_week_list = list(base_sales_qs.filter(date_added__gte=start_of_week, date_added__lt=end_of_week))
        transaction = len(sales_week_list)
        
        for d in range(0, 7):
            target_date = start_of_week + timedelta(days=d)
            if target_date > today_start:
                break
                
            daily_revenue = sum(s.grand_total for s in sales_week_list if timezone.localtime(s.date_added).date() == target_date.date())
            
            day_names = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
            sales_dates.append(f"{day_names[d]} {target_date.day}")
            sales_amounts.append(float(daily_revenue))
            
        chart_total_val = sum(sales_amounts)
        
        start_of_last_week = start_of_week - timedelta(days=7)
        
        last_week_total_agg = base_sales_qs.filter(date_added__gte=start_of_last_week, date_added__lt=start_of_week).aggregate(Sum('grand_total'))['grand_total__sum']
        last_week_total = float(last_week_total_agg) if last_week_total_agg else 0.0
        
        if last_week_total > 0:
            chart_pct = ((chart_total_val - last_week_total) / last_week_total) * 100
        else:
            chart_pct = 100.0 if chart_total_val > 0 else 0.0

    elif filter_chart == 'tahun_ini':
        selected_period_name = f"Tahun Ini ({current_year})"
        chart_title = f"Periode {selected_period_name}"
        year_start = today_start.replace(month=1, day=1)
        next_year_start = year_start.replace(year=year_start.year+1)
        
        sales_year_list = list(base_sales_qs.filter(date_added__gte=year_start, date_added__lt=next_year_start))
        transaction = len(sales_year_list)
        
        for m in range(1, int(current_month) + 1):
            monthly_revenue = sum(s.grand_total for s in sales_year_list if timezone.localtime(s.date_added).month == m)
            
            month_name = date(int(current_year), m, 1).strftime('%b')
            sales_dates.append(month_name)
            sales_amounts.append(float(monthly_revenue))
            
        chart_total_val = sum(sales_amounts)

        if len(sales_amounts) >= 2:
            first_val = sales_amounts[0]
            last_val = sales_amounts[-1]
            diff = last_val - first_val
            if first_val > 0:
                chart_pct = (diff / first_val) * 100
            else:
                chart_pct = 100.0 if diff > 0 else 0.0
        else:
            chart_pct = 0.0

    else:
        # Default: Bulan Ini
        selected_period_name = f"Bulan Ini ({now.strftime('%B %Y')})"
        chart_title = f"Periode {selected_period_name}"
        num_days = calendar.monthrange(int(current_year), int(current_month))[1]
        
        sales_month_list = list(base_sales_qs.filter(date_added__gte=month_start, date_added__lt=next_month_start))
        transaction = len(sales_month_list)
        
        for d in range(1, num_days + 1):
            target_date = month_start.replace(day=d)
            if target_date > today_start: 
                break 
            
            daily_revenue = sum(s.grand_total for s in sales_month_list if timezone.localtime(s.date_added).day == d)
            
            sales_dates.append(f"{d} {now.strftime('%b')}")
            sales_amounts.append(float(daily_revenue))
            
        chart_total_val = sum(sales_amounts)
        
        rev_last_month_agg = base_sales_qs.filter(date_added__gte=last_month_start, date_added__lt=month_start).aggregate(Sum('grand_total'))['grand_total__sum']
        rev_last_month = rev_last_month_agg if rev_last_month_agg else 0
        
        if rev_last_month > 0:
            chart_pct = ((chart_total_val - rev_last_month) / rev_last_month) * 100
        else:
            chart_pct = 100.0 if chart_total_val > 0 else 0.0

    chart_growth_pct = f"+{chart_pct:.2f}" if chart_pct > 0 else f"{chart_pct:.2f}"
    is_chart_positive = chart_pct >= 0

    # =======================================================
    # 2.5 KALKULASI LABA BERSIH (NET PROFIT)
    # =======================================================
    # Tentukan rentang waktu berdasarkan filter
    if filter_chart == 'hari_ini':
        start_date = today_start; end_date = today_end
        current_period_sales = sales_today_list
    elif filter_chart == 'minggu_ini':
        start_date = start_of_week; end_date = end_of_week
        current_period_sales = sales_week_list
    elif filter_chart == 'tahun_ini':
        start_date = year_start; end_date = next_year_start
        current_period_sales = sales_year_list
    else:
        start_date = month_start; end_date = next_month_start
        current_period_sales = sales_month_list
        
    sale_ids = [s.id for s in current_period_sales]
    
    # Hitung total HPP
    hpp_agg = salesItems.objects.filter(sale_id__in=sale_ids).aggregate(
        total_hpp=Sum(F('qty') * F('hpp'))
    )
    total_hpp_terjual = hpp_agg['total_hpp'] if hpp_agg['total_hpp'] else 0.0
    
    # Hitung total Garansi (berdasarkan tanggal garansi diajukan)
    warranty_agg = WarrantyClaim.objects.filter(date_added__gte=start_date, date_added__lt=end_date).aggregate(
        total_cost=Sum('cost')
    )
    total_biaya_garansi = warranty_agg['total_cost'] if warranty_agg['total_cost'] else 0.0
    
    chart_net_profit = chart_total_val - total_hpp_terjual - total_biaya_garansi


    # =======================================================
    # 3. PRODUK TERLARIS
    # =======================================================
    filter_terlaris = request.GET.get('filter_terlaris', 'hari_ini')
    qs_terlaris = salesItems.objects.all()

    if filter_terlaris == 'bulan_ini':
        qs_terlaris = qs_terlaris.filter(sale_id__date_added__gte=month_start, sale_id__date_added__lt=next_month_start)
    elif filter_terlaris == 'tahun_ini':
        year_start = today_start.replace(month=1, day=1)
        next_year_start = year_start.replace(year=year_start.year+1)
        qs_terlaris = qs_terlaris.filter(sale_id__date_added__gte=year_start, sale_id__date_added__lt=next_year_start)
    elif filter_terlaris == 'minggu_ini':
        start_of_week = today_start - timedelta(days=today_start.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        qs_terlaris = qs_terlaris.filter(sale_id__date_added__gte=start_of_week, sale_id__date_added__lt=end_of_week)
    else:
        qs_terlaris = qs_terlaris.filter(sale_id__date_added__gte=today_start, sale_id__date_added__lt=today_end)

    top_products = qs_terlaris.values('product_id__id', 'product_id__name', 'product_id__code', 'product_id__category_id__name') \
     .annotate(total_qty=Sum('qty')) \
     .order_by('-total_qty')[:5]

    low_stock = Products.objects.filter(stock__lte=5, status=1).order_by('stock')[:5]
    
    # Transaksi terakhir spesifik untuk kasir yang sedang login
    if request.user.is_superuser:
        recent_sales = Sales.objects.all().order_by('-date_added')[:5]
    else:
        recent_sales = Sales.objects.filter(cashier=request.user).order_by('-date_added')[:5]

    context = {
        'page_title': 'Home',
        'categories': categories,
        'products': products,
        'transaction': transaction,
        'total_sales': int(chart_total_val),
        
        # Variabel Grafik Saham
        'chart_title': chart_title,
        'selected_period_name': selected_period_name,
        'chart_total_val': int(chart_total_val),
        'chart_net_profit': int(chart_net_profit),
        'chart_growth_pct': chart_growth_pct,
        'is_chart_positive': is_chart_positive,
        'sales_dates': sales_dates,
        'sales_amounts': sales_amounts,
        
        'top_products': top_products,
        'low_stock': low_stock,
        'recent_sales': recent_sales,
    }
    return render(request, 'posApp/home.html', context)


def about(request):
    context = {
        'page_title':'About',
    }
    return render(request, 'posApp/about.html',context)


# ==========================================
# CATEGORIES
# ==========================================
@login_required
def category(request):
    category_list = Category.objects.all()
    context = {
        'page_title':'Category List',
        'category':category_list,
    }
    return render(request, 'posApp/category.html',context)

@login_required
@user_passes_test(is_admin, login_url='/')
def manage_category(request):
    category = {}
    category_types = []
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            category = Category.objects.filter(id=id).first()
            if category:
                from posApp.models import CategoryType
                category_types = CategoryType.objects.filter(category=category)
    
    context = {
        'category' : category,
        'category_types': category_types
    }
    return render(request, 'posApp/manage_category.html',context)

@login_required
@user_passes_test(is_admin, login_url='/')
def save_category(request):
    data =  request.POST
    files = request.FILES
    resp = {'status':'failed'}
    try:
        if (data['id']).isnumeric() and int(data['id']) > 0 :
            # MODE UPDATE
            cat = Category.objects.filter(id=data['id']).first()
            cat.name = data['name']
            
            # Remove legacy type strings from description if they exist
            desc = data['description']
            if '|||' in desc:
                desc = desc.split('|||')[0]
            cat.description = desc
            
            cat.status = data['status']
            if 'image' in files:
                cat.image = files['image']
            cat.save()
        else:
            # MODE TAMBAH BARU
            desc = data['description']
            if '|||' in desc:
                desc = desc.split('|||')[0]
                
            cat = Category(name=data['name'], description=desc, status=data['status'])
            if 'image' in files:
                cat.image = files['image']
            cat.save()
            
        # PROSES CATEGORY TYPES
        from posApp.models import CategoryType
        type_names = data.get('type_names_list', '').split('|||')
        type_names = [t.strip() for t in type_names if t.strip()]
        
        # Simpan atau update tipe
        existing_types = CategoryType.objects.filter(category=cat)
        existing_names = [t.name for t in existing_types]
        
        # Hapus tipe yang tidak ada di form
        for et in existing_types:
            if et.name not in type_names:
                et.delete()
                
        # Tambah atau update gambar
        for idx, t_name in enumerate(type_names):
            ctype, created = CategoryType.objects.get_or_create(category=cat, name=t_name)
            
            # File dikirim dengan key type_img_0, type_img_1, dst.
            file_key = f'type_img_{idx}'
            if file_key in files:
                ctype.image = files[file_key]
                ctype.save()
            
        resp['status'] = 'success'
        messages.success(request, 'Category Successfully saved.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_passes_test(is_admin, login_url='/')
def delete_category(request):
    data =  request.POST
    resp = {'status':''}
    try:
        Category.objects.filter(id = data['id']).delete()
        resp['status'] = 'success'
        messages.success(request, 'Category Successfully deleted.')
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


# ==========================================
# PRODUCTS
# ==========================================
@login_required
def products(request):
    product_list = Products.objects.all()
    context = {
        'page_title':'Product List',
        'products':product_list,
    }
    return render(request, 'posApp/products.html',context)

@login_required
@user_passes_test(is_admin, login_url='/')
def manage_products(request):
    product = {}
    categories = Category.objects.filter(status = 1).prefetch_related('types')
    
    # Hitung global sequence (Jumlah produk keseluruhan + 1)
    global_next_seq = Products.objects.count() + 1
        
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            product = Products.objects.filter(id=id).first()
    
    context = {
        'product' : product,
        'categories' : categories,
        'global_next_seq': global_next_seq
    }
    return render(request, 'posApp/manage_product.html',context)

def test(request):
    categories = Category.objects.all()
    context = {
        'categories' : categories
    }
    return render(request, 'posApp/test.html',context)

@login_required
@user_passes_test(is_admin, login_url='/')
def save_product(request):
    data = request.POST
    files = request.FILES 
    resp = {'status':'failed'}
    id = ''
    
    if 'id' in data:
        id = data['id']
        
    if id.isnumeric() and int(id) > 0:
        check = Products.objects.exclude(id=id).filter(code=data['code']).all()
    else:
        check = Products.objects.filter(code=data['code']).all()
        
    if len(check) > 0 :
        resp['msg'] = "Kode SKU sudah digunakan oleh produk lain."
    else:
        category = Category.objects.filter(id = data['category_id']).first()
        try:
            # ==========================================
            # PENCEGAHAN NILAI KOSONG (ANTI-ERROR)
            # ==========================================
            if 'stock' in data:
                stock_input = data.get('stock', 0)
                if stock_input == '': stock_input = 0
            else:
                stock_input = None
            
            warranty_input = data.get('warranty', 0)
            if warranty_input == '': warranty_input = 0
            
            price_input = data.get('price', 0)
            if price_input == '': price_input = 0
            clean_price = str(price_input).replace(',', '').replace('.', '')
            try:
                final_price = float(clean_price)
            except:
                final_price = 0.0
            # ==========================================

            if id.isnumeric() and int(id) > 0 :
                # MODE UPDATE
                prod = Products.objects.filter(id=id).first()
                prod.code = data['code']
                prod.category_id = category
                prod.name = data['name']
                prod.description = data['description']
                prod.price = final_price
                if 'hpp' in data:
                    prod.hpp = float(data['hpp'])
                prod.status = data['status']
                if stock_input is not None:
                    prod.stock = int(stock_input)
                prod.warranty = int(warranty_input)
                
                if 'image' in files:
                    prod.image = files['image']
                prod.save()
            else:
                # MODE TAMBAH BARU
                prod = Products(
                    code=data['code'], 
                    category_id=category, 
                    name=data['name'], 
                    description=data['description'], 
                    price=final_price,
                    hpp=float(data.get('hpp', 0)),
                    status=data['status'],
                    stock=int(stock_input) if stock_input is not None else 0,
                    warranty=int(warranty_input)
                )
                if 'image' in files:
                    prod.image = files['image']
                prod.save()
                
            resp['status'] = 'success'
            resp['product'] = {
                'id': prod.id,
                'code': prod.code,
                'name': f"{category.name} {prod.name}" if category else prod.name,
                'price': float(prod.price)
            }
        except Exception as e:
            resp['status'] = 'failed'
            resp['msg'] = str(e)
            
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_passes_test(is_admin, login_url='/')
def delete_product(request):
    data =  request.POST
    resp = {'status':''}
    try:
        Products.objects.filter(id = data['id']).delete()
        resp['status'] = 'success'
    except:
        resp['status'] = 'failed'
    return HttpResponse(json.dumps(resp), content_type="application/json")


# ==========================================
# INVENTORY
# ==========================================
@login_required
@user_passes_test(is_admin, login_url='/')
def inventory(request):
    product_list = Products.objects.all()
    
    # Hitung potensi profit
    total_hpp_asset = sum([(p.hpp or 0) * (p.stock or 0) for p in product_list])
    total_sales_asset = sum([(p.price or 0) * (p.stock or 0) for p in product_list])
    potential_profit = total_sales_asset - total_hpp_asset
    
    context = {
        'page_title':'Inventory List',
        'products':product_list,
        'total_hpp_asset': total_hpp_asset,
        'total_sales_asset': total_sales_asset,
        'potential_profit': potential_profit
    }
    return render(request, 'posApp/inventory.html', context)

@login_required
@user_passes_test(is_admin, login_url='/')
def manage_inventory(request):
    product = {}
    if request.method == 'GET':
        data =  request.GET
        id = ''
        if 'id' in data:
            id= data['id']
        if id.isnumeric() and int(id) > 0:
            product = Products.objects.filter(id=id).first()
    
    context = {
        'product' : product
    }
    return render(request, 'posApp/manage_inventory.html',context)

@login_required
@user_passes_test(is_admin, login_url='/')
def save_inventory(request):
    data = request.POST
    resp = {'status':'failed'}
    try:
        id = data.get('id', '')
        if id.isnumeric() and int(id) > 0 :
            prod = Products.objects.filter(id=id).first()
            if prod:
                stock_input = data.get('stock', 0)
                if stock_input == '': stock_input = 0
                prod.stock = int(stock_input)
                prod.save()
                resp['status'] = 'success'
            else:
                resp['msg'] = 'Produk tidak ditemukan.'
        else:
            resp['msg'] = 'ID Produk tidak valid.'
    except Exception as e:
        resp['status'] = 'failed'
        resp['msg'] = str(e)
            
    return HttpResponse(json.dumps(resp), content_type="application/json")


# ==========================================
# BARANG MASUK (PURCHASES)
# ==========================================
@login_required
@user_passes_test(is_admin, login_url='/')
def purchases(request):
    purchase_data = Purchases.objects.all().order_by('-date_added')
    purchase_list = []
    for p in purchase_data:
        items = purchaseItems.objects.filter(purchase_id=p).all()
        purchase_list.append({
            'id': p.id,
            'code': p.code,
            'supplier_name': p.supplier_id.name,
            'supplier_wa': p.supplier_id.contact,
            'supplier_address': p.supplier_id.address,
            'grand_total': p.grand_total,
            'date_added': p.date_added,
            'product_items': items
        })
    context = {
        'page_title': 'Riwayat Barang Masuk',
        'purchase_data': purchase_list,
    }
    return render(request, 'posApp/purchases.html', context)

@login_required
@user_passes_test(is_admin, login_url='/')
def new_purchase(request):
    products = Products.objects.filter(status=1)
    suppliers = Supplier.objects.filter(status=1)
    
    # Jika belum ada supplier, buat satu supplier default
    if suppliers.count() == 0:
        default_supplier = Supplier(name="Pemasok Umum")
        default_supplier.save()
        suppliers = Supplier.objects.filter(status=1)
        
    context = {
        'page_title': "Penerimaan Barang Masuk",
        'products': products,
        'suppliers': suppliers
    }
    return render(request, 'posApp/new_purchase.html', context)

@login_required
@user_passes_test(is_admin, login_url='/')
def save_purchase(request):
    resp = {'status': 'failed'}
    try:
        data = request.POST
        import string
        import random
        
        # Generate Purchase Code
        code = ''
        while True:
            code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
            if Purchases.objects.filter(code=code).count() == 0:
                break
                
        supplier_name = data.get('supplier_name')
        
        if not supplier_name or str(supplier_name).strip() == '':
            resp['msg'] = 'Nama Supplier tidak boleh kosong.'
            return HttpResponse(json.dumps(resp), content_type="application/json")
            
        supplier_name = str(supplier_name).strip()
        supplier_contact = data.get('supplier_contact', '').strip()
        supplier_address = data.get('supplier_address', '').strip()
        
        # Cek apakah supplier dengan nama ini sudah ada (case-insensitive)
        supplier = Supplier.objects.filter(name__iexact=supplier_name).first()
        
        # Jika belum ada, buat baru
        if not supplier:
            supplier = Supplier(name=supplier_name, status=1, contact=supplier_contact, address=supplier_address)
            supplier.save()
        else:
            # Update kontak/alamat jika sebelumnya kosong
            updated = False
            if supplier_contact and not supplier.contact:
                supplier.contact = supplier_contact
                updated = True
            if supplier_address and not supplier.address:
                supplier.address = supplier_address
                updated = True
            if updated:
                supplier.save()
            
        grand_total = data.get('grand_total', 0)
        
        purchase = Purchases(code=code, supplier_id=supplier, grand_total=float(grand_total))
        purchase.save()
        
        # Process Items
        for i in range(len(data.getlist('product_id[]'))):
            prod_id = data.getlist('product_id[]')[i]
            
            raw_qty = data.getlist('qty[]')[i]
            qty = float(raw_qty) if raw_qty and str(raw_qty).strip() != '' else 0.0
            
            raw_price = data.getlist('price[]')[i]
            clean_price = str(raw_price).replace(',', '').replace('.', '').strip()
            price = float(clean_price) if clean_price != '' else 0.0
            
            total = qty * price
            
            product = Products.objects.filter(id=prod_id).first()
            if product:
                # 1. Simpan item masuk
                item = purchaseItems(purchase_id=purchase, product_id=product, price=float(price), qty=float(qty), total=total)
                item.save()
                
                # 2. Tambahkan stok produk & Update HPP (Weighted Average Cost)
                old_stock = product.stock if product.stock else 0
                old_hpp = product.hpp if product.hpp else 0
                new_qty = int(qty)
                if (old_stock + new_qty) > 0:
                    product.hpp = ((old_stock * old_hpp) + (new_qty * price)) / (old_stock + new_qty)
                else:
                    product.hpp = price
                product.stock = old_stock + new_qty
                product.save()
                
        resp['status'] = 'success'
        resp['purchase_id'] = purchase.id
    except Exception as e:
        resp['status'] = 'failed'
        resp['msg'] = str(e)

    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_passes_test(is_admin, login_url='/')
def delete_purchase(request):
    resp = {'status': 'failed'}
    try:
        data = request.POST
        purchase = Purchases.objects.filter(id=data['id']).first()
        if purchase:
            # Kembalikan stok
            items = purchaseItems.objects.filter(purchase_id=purchase)
            for item in items:
                prod = item.product_id
                if prod.stock is None:
                    prod.stock = 0
                prod.stock -= int(item.qty)
                prod.save()
                
            purchase.delete()
            resp['status'] = 'success'
        else:
            resp['msg'] = 'Data tidak ditemukan.'
    except Exception as e:
        resp['status'] = 'failed'
        resp['msg'] = str(e)
    return HttpResponse(json.dumps(resp), content_type="application/json")


# ==========================================
# POS (KASIR & ADMIN BEBAS)
# ==========================================
@login_required
def pos(request):
    products = Products.objects.filter(status=1, stock__gt=0)
    product_json = []
    for product in products:
        product_json.append({
            'id': product.id, 
            'name': product.name, 
            'price': float(product.price),
            'stock': product.stock or 0
        })
    context = {
        'page_title' : "Point of Sale",
        'products' : products,
        'product_json' : json.dumps(product_json)
    }
    return render(request, 'posApp/pos.html',context)

@login_required
def checkout_modal(request):
    grand_total = 0
    if 'grand_total' in request.GET:
        grand_total = request.GET['grand_total']
    context = {
        'grand_total' : grand_total,
    }
    return render(request, 'posApp/checkout.html',context)

@login_required
def save_pos(request):
    resp = {'status':'failed','msg':''}
    data = request.POST
    pref = datetime.now().year  # Prefix = Tahun saat ini (misal: 2025)
    i = 1
    while True:
        code = '{:0>5}'.format(i)
        i += int(1)
        check = Sales.objects.filter(code = str(pref) + str(code)).all()
        if len(check) <= 0:
            break
    code = str(pref) + str(code)

    try:
        payment = data.get('payment_method', 'Tunai')
        
        grand_total_val = float(data.get('grand_total', 0))
        tendered_amount_val = float(data.get('tendered_amount', 0))
        amount_change_val = float(data.get('amount_change', 0))

        if payment.lower() == 'qris':
            tendered_amount_val = grand_total_val
            amount_change_val = 0.0 

        # ==========================================
        # PENYIMPANAN DATA SALES (TERMASUK CUSTOMER)
        # ==========================================
        sales = Sales(
            code=code, 
            sub_total=data.get('sub_total', 0), 
            diskon=data.get('diskon', 0), 
            diskon_amount=data.get('diskon_amount', 0), 
            grand_total=grand_total_val, 
            tendered_amount=tendered_amount_val, 
            amount_change=amount_change_val,     
            payment_method=payment,
            # TANGKAP DATA PELANGGAN DARI FORM HTML
            customer_name=data.get('customer_name', ''),
            customer_wa=data.get('customer_wa', ''),
            customer_address=data.get('customer_address', ''),
            # KASIR YANG MEMPROSES
            cashier=request.user
        )
        sales.save()
        sale_id = sales.pk
        
        i = 0
        for prod in data.getlist('product_id[]'):
            product_id = prod 
            sale = Sales.objects.filter(id=sale_id).first()
            product = Products.objects.filter(id=product_id).first()
            qty = data.getlist('qty[]')[i] 
            price = data.getlist('price[]')[i] 
            total = float(qty) * float(price)
            
            if product:
                product.stock = product.stock - int(float(qty))
                product.save()

            item_hpp = product.hpp if product and product.hpp else 0
            salesItems(sale_id = sale, product_id = product, qty = qty, price = price, hpp = item_hpp, total = total).save()
            i += int(1)
            
        resp['status'] = 'success'
        resp['sale_id'] = sale_id
        
    except Exception as e:
        resp['msg'] = "An error occured: " + str(e)
        print("Unexpected error:", sys.exc_info()[0])
        
    return HttpResponse(json.dumps(resp),content_type="application/json")


# ==========================================
# SALES TRANSACTIONS
# ==========================================
@login_required
def salesList(request):
    # Mengambil data dari yang pertama sampai akhir
    sales = Sales.objects.all().order_by('id')
    sale_data = []
    for sale in sales:
        data = {}
        for field in sale._meta.get_fields(include_parents=False):
            if field.related_model is None:
                data[field.name] = getattr(sale,field.name)
        
        # Tambahan info Kasir
        if sale.cashier:
            data['cashier_name'] = sale.cashier.first_name if sale.cashier.first_name else sale.cashier.username
        else:
            data['cashier_name'] = 'Admin'

        data['items'] = salesItems.objects.filter(sale_id = sale).all()
        data['item_count'] = len(data['items'])
        
        # Hitung Total HPP dari transaksi ini (menggunakan hpp yang dibekukan)
        total_hpp = sum((item.qty * (item.hpp or 0)) for item in data['items'])
        data['total_hpp'] = total_hpp
        
        # Hitung Biaya Garansi jika ada klaim untuk struk ini
        warranties = WarrantyClaim.objects.filter(sale_id=sale)
        total_warranty = sum(w.cost for w in warranties)
        data['total_warranty'] = total_warranty

        # Buat map: product_id -> info klaim (untuk badge "Sudah Diklaim" di kolom garansi)
        claimed_map = {}
        for w in warranties:
            claimed_map[w.product_id.id] = {
                'date': w.date_added.strftime('%d/%m/%Y'),
                'description': w.description,
                'cost': int(w.cost),
                'status': w.status,  # 0=Proses, 1=Selesai
            }

        # Enriching setiap item dengan status klaim
        enriched_items = list(data['items'])
        for item in enriched_items:
            item.is_claimed = item.product_id.id in claimed_map
            item.claim_info = claimed_map.get(item.product_id.id, {})
        data['items'] = enriched_items

        # Laba Bersih
        data['net_profit'] = sale.grand_total - total_hpp - total_warranty
        
        if 'diskon_amount' in data:
            data['diskon_amount'] = float(data['diskon_amount'])
        sale_data.append(data)
    context = {
        'page_title':'Sales Transactions',
        'sale_data':sale_data,
    }
    return render(request, 'posApp/sales.html',context)

@login_required
def receipt(request):
    id = request.GET.get('id')
    sales = Sales.objects.filter(id = id).first()
    transaction = {}
    
    for field in Sales._meta.get_fields():
        if field.related_model is None:
            transaction[field.name] = getattr(sales,field.name)
            
    if sales.cashier:
        transaction['cashier_name'] = sales.cashier.first_name if sales.cashier.first_name else sales.cashier.username
    else:
        transaction['cashier_name'] = 'Admin'

    if 'diskon_amount' in transaction:
        transaction['diskon_amount'] = float(transaction['diskon_amount'])
        
    ItemList = salesItems.objects.filter(sale_id = sales).all()
    context = {
        "transaction" : transaction,
        "salesItems" : ItemList
    }
    return render(request, 'posApp/receipt.html',context)

@login_required
@user_passes_test(is_admin, login_url='/')
def delete_sale(request):
    resp = {'status':'failed', 'msg':''}
    id = request.POST.get('id')
    try:
        sale_items = salesItems.objects.filter(sale_id=id)
        for item in sale_items:
            product = item.product_id
            if product:
                product.stock += int(float(item.qty))
                product.save()

        delete = Sales.objects.filter(id = id).delete()
        resp['status'] = 'success'
    except:
        resp['msg'] = "An error occured"
        print("Unexpected error:", sys.exc_info()[0])
    return HttpResponse(json.dumps(resp), content_type='application/json')


# ==========================================
# API PENGINTAI TRANSAKSI BARU (AJAX POLLING)
# ==========================================
@login_required
def check_new_sales(request):
    last_id = request.GET.get('last_id', 0)
    try:
        last_id = int(last_id)
        new_sales = Sales.objects.filter(id__gt=last_id).order_by('id')
        
        if new_sales.exists():
            latest_sale = new_sales.last()
            return JsonResponse({
                'has_new': True,
                'last_id': latest_sale.id,
                'message': f'Transaksi baru: {latest_sale.code}'
            })
            
    except Exception as e:
        pass
        
    return JsonResponse({'has_new': False})

# ==========================================
# KLAIM GARANSI (WARRANTY CLAIMS)
# ==========================================
@login_required
def warranties(request):
    from .models import WarrantyClaim
    claims = WarrantyClaim.objects.all().order_by('-date_added')
    total_cost = sum([c.cost for c in claims])
    context = {
        'page_title': 'Klaim Garansi & Servis',
        'claims': claims,
        'total_cost': total_cost
    }
    return render(request, 'posApp/warranties.html', context)

@login_required
def manage_warranty(request):
    from .models import WarrantyClaim
    claim = {}
    sales = Sales.objects.all().order_by('-date_added')
    if request.GET.get('id'):
        claim = WarrantyClaim.objects.get(id=request.GET.get('id'))
    context = {
        'claim': claim,
        'sales': sales
    }
    return render(request, 'posApp/manage_warranty.html', context)

@login_required
def get_sale_items(request):
    sale_id = request.GET.get('sale_id')
    items = salesItems.objects.filter(sale_id=sale_id)
    resp = []
    try:
        sale_obj = Sales.objects.get(id=sale_id)
    except Sales.DoesNotExist:
        return HttpResponse(json.dumps([]), content_type="application/json")

    for item in items:
        brand = item.product_id.category_id.name if item.product_id.category_id else ''
        full_name = f"[{brand}] {item.product_id.name}" if brand else item.product_id.name
        warranty_days = item.product_id.warranty or 0

        # Cek apakah sudah pernah diklaim (dari struk ini)
        is_claimed = WarrantyClaim.objects.filter(
            sale_id=sale_obj, product_id=item.product_id
        ).exists()

        # Hitung sisa hari garansi
        days_remaining = None
        is_expired = False
        expiry_date_str = None
        if warranty_days > 0:
            expiry_dt = sale_obj.date_added + timedelta(days=warranty_days)
            expiry_date_str = expiry_dt.strftime('%d/%m/%Y')
            remaining = (expiry_dt - timezone.now()).days
            days_remaining = remaining
            is_expired = remaining < 0

        resp.append({
            'id': item.product_id.id,
            'name': full_name,
            'warranty_days': warranty_days,
            'is_claimed': is_claimed,
            'is_expired': is_expired,
            'days_remaining': days_remaining,
            'expiry_date': expiry_date_str,
        })
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
def save_warranty(request):
    from .models import WarrantyClaim
    resp = {'status':'failed', 'msg':''}
    data = request.POST
    try:
        sale = Sales.objects.get(id=data['sale_id'])
        product = Products.objects.get(id=data['product_id'])
        claim_id = data.get('id')

        # ============================================================
        # VALIDASI: Cek duplikat klaim (hanya untuk klaim BARU)
        # ============================================================
        if not claim_id:
            already_claimed = WarrantyClaim.objects.filter(
                sale_id=sale, product_id=product
            ).exists()
            if already_claimed:
                resp['msg'] = (
                    f'Garansi produk "{product.name}" dari struk {sale.code} '
                    f'sudah pernah diklaim sebelumnya. Satu produk hanya dapat diklaim satu kali.'
                )
                return HttpResponse(json.dumps(resp), content_type="application/json")

            # ============================================================
            # VALIDASI: Cek masa berlaku garansi (hanya jika produk bergaransi)
            # ============================================================
            warranty_days = product.warranty or 0
            if warranty_days > 0:
                expiry_dt = sale.date_added + timedelta(days=warranty_days)
                if timezone.now() > expiry_dt:
                    expiry_str = expiry_dt.strftime('%d/%m/%Y')
                    resp['msg'] = (
                        f'Masa garansi produk "{product.name}" sudah habis sejak {expiry_str}. '
                        f'Garansi tidak dapat diklaim lagi.'
                    )
                    return HttpResponse(json.dumps(resp), content_type="application/json")

        if claim_id:
            # Update klaim yang sudah ada
            claim = WarrantyClaim.objects.get(id=claim_id)
            claim.sale_id = sale
            claim.product_id = product
            claim.description = data['description']
            claim.cost = float(str(data['cost']).replace(',', '').replace('.', ''))
            claim.status = int(data['status'])
            claim.save()
        else:
            # Buat klaim baru
            claim = WarrantyClaim(
                sale_id=sale,
                product_id=product,
                description=data['description'],
                cost=float(str(data['cost']).replace(',', '').replace('.', '')),
                status=int(data['status'])
            )
            claim.save()
        resp['status'] = 'success'
        messages.success(request, "Data klaim garansi berhasil disimpan.")
    except Exception as e:
        resp['msg'] = str(e)
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_passes_test(is_admin, login_url='/')
def delete_warranty(request):
    from .models import WarrantyClaim
    resp = {'status':'failed', 'msg':''}
    id = request.POST.get('id')
    try:
        WarrantyClaim.objects.filter(id=id).delete()
        resp['status'] = 'success'
        messages.success(request, "Data klaim garansi berhasil dihapus.")
    except Exception as e:
        resp['msg'] = str(e)
    return HttpResponse(json.dumps(resp), content_type="application/json")

# ==========================================
# MODUL MANAJEMEN RETUR & BARANG CACAT
# ==========================================
@login_required
@user_passes_test(is_admin, login_url='/')
def returns_list(request):
    from .models import Returns
    returns = Returns.objects.all().order_by('-date_added')
    context = {
        'page_title': 'Manajemen Retur & Barang Cacat',
        'returns': returns,
    }
    return render(request, 'posApp/returns.html', context)

@login_required
@user_passes_test(is_admin, login_url='/')
def manage_return(request):
    from .models import Returns, Purchases
    ret_obj = {}
    products = Products.objects.filter(status=1)
    purchases = Purchases.objects.all().order_by('-date_added')
    
    if request.method == 'GET':
        id = request.GET.get('id', '')
        if id.isnumeric() and int(id) > 0:
            ret_obj = Returns.objects.filter(id=id).first()
            
    context = {
        'ret_obj': ret_obj,
        'products': products,
        'purchases': purchases
    }
    return render(request, 'posApp/manage_return.html', context)

@login_required
@user_passes_test(is_admin, login_url='/')
def save_return(request):
    from .models import Returns
    data = request.POST
    resp = {'status':'failed', 'msg':''}
    try:
        id = data.get('id', '')
        product = Products.objects.get(id=data['product_id'])
        
        supplier = None
        if data.get('supplier_id'):
            supplier = Supplier.objects.get(id=data['supplier_id'])
            
        qty = int(data['qty'])
        if qty <= 0:
            raise Exception("Kuantitas harus lebih dari 0")
            
        if id and int(id) > 0:
            # Update
            ret_obj = Returns.objects.get(id=id)
            old_qty = ret_obj.qty
            old_product = ret_obj.product_id
            
            # Kembalikan stok lama dulu (rollback sementara)
            old_product.stock += old_qty
            old_product.save()
            
            # Refresh product dari DB agar stok akurat
            product.refresh_from_db()
            
            # Validasi stok baru mencukupi
            if product.stock < qty:
                # Batalkan rollback
                old_product.stock -= old_qty
                old_product.save()
                raise Exception(f"Stok tidak cukup! Stok tersedia: {product.stock}")
                
            # Kurangi dengan qty baru
            product.stock -= qty
            product.save()
            
            ret_obj.product_id = product
            ret_obj.supplier_id = supplier
            ret_obj.type = data['type']
            ret_obj.qty = qty
            ret_obj.reason = data['reason']
            ret_obj.save()
        else:
            # Create
            if product.stock < qty:
                raise Exception(f"Stok tidak cukup! Stok saat ini: {product.stock}")
            product.stock -= qty
            product.save()
            
            ret_obj = Returns(
                product_id=product,
                supplier_id=supplier,
                type=data['type'],
                qty=qty,
                reason=data['reason']
            )
            ret_obj.save()
            
        resp['status'] = 'success'
        messages.success(request, "Data retur berhasil disimpan dan stok disesuaikan.")
    except Exception as e:
        resp['msg'] = str(e)
    return HttpResponse(json.dumps(resp), content_type="application/json")

@login_required
@user_passes_test(is_admin, login_url='/')
def delete_return(request):
    from .models import Returns
    resp = {'status':'failed', 'msg':''}
    id = request.POST.get('id')
    try:
        ret_obj = Returns.objects.get(id=id)
        product = ret_obj.product_id
        product.stock += ret_obj.qty
        product.save()
        
        ret_obj.delete()
        resp['status'] = 'success'
        messages.success(request, "Retur dibatalkan, stok dikembalikan.")
    except Exception as e:
        resp['msg'] = str(e)
    return HttpResponse(json.dumps(resp), content_type="application/json")


# ==========================================
# MODUL LAPORAN (SKRIPSI)
# ==========================================
@login_required
@user_passes_test(is_admin, login_url='/')
def reports(request):
    from django.utils import timezone
    from .models import Returns, Purchases, purchaseItems

    # --- Filter Tanggal ---
    date_from_str = request.GET.get('date_from', '')
    date_to_str   = request.GET.get('date_to', '')

    try:
        date_from = timezone.make_aware(datetime.strptime(date_from_str, '%Y-%m-%d'))
    except:
        date_from = timezone.make_aware(datetime(timezone.now().year, timezone.now().month, 1))

    try:
        date_to = timezone.make_aware(datetime.strptime(date_to_str, '%Y-%m-%d')) + timedelta(days=1)
    except:
        date_to = timezone.now() + timedelta(days=1)

    # -----------------------------------------------
    # 1. LAPORAN LABA RUGI
    # -----------------------------------------------
    sales_qs = Sales.objects.filter(date_added__gte=date_from, date_added__lt=date_to)
    total_penjualan = sum(s.grand_total for s in sales_qs)

    all_items = salesItems.objects.filter(sale_id__in=sales_qs)
    total_hpp = sum(item.qty * (item.product_id.hpp or 0) for item in all_items)

    warranties_qs = WarrantyClaim.objects.filter(date_added__gte=date_from, date_added__lt=date_to)
    total_garansi = sum(w.cost for w in warranties_qs)

    laba_kotor  = total_penjualan - total_hpp
    laba_bersih = laba_kotor - total_garansi

    laba_rugi = {
        'total_penjualan': total_penjualan,
        'total_hpp':       total_hpp,
        'laba_kotor':      laba_kotor,
        'total_garansi':   total_garansi,
        'laba_bersih':     laba_bersih,
        'jumlah_transaksi': sales_qs.count(),
    }

    # -----------------------------------------------
    # 2. LAPORAN MUTASI STOK
    # -----------------------------------------------
    products_all = Products.objects.all()
    mutasi_list = []
    for prod in products_all:
        masuk_items = purchaseItems.objects.filter(
            product_id=prod,
            purchase_id__date_added__gte=date_from,
            purchase_id__date_added__lt=date_to
        )
        keluar_items = salesItems.objects.filter(
            product_id=prod,
            sale_id__date_added__gte=date_from,
            sale_id__date_added__lt=date_to
        )
        retur_items = Returns.objects.filter(
            product_id=prod,
            date_added__gte=date_from,
            date_added__lt=date_to
        )
        total_masuk  = sum(i.qty for i in masuk_items)
        total_keluar = sum(i.qty for i in keluar_items)
        total_retur  = sum(r.qty for r in retur_items)

        if total_masuk > 0 or total_keluar > 0 or total_retur > 0:
            mutasi_list.append({
                'product': prod,
                'total_masuk':  total_masuk,
                'total_keluar': total_keluar,
                'total_retur':  total_retur,
                'stok_akhir':   prod.stock or 0,
            })

    # -----------------------------------------------
    # 3. REKAP BARANG MASUK PER SUPPLIER
    # -----------------------------------------------
    purchases_qs = Purchases.objects.filter(date_added__gte=date_from, date_added__lt=date_to).order_by('-date_added')
    supplier_rekap = {}
    for p in purchases_qs:
        s_name = p.supplier_id.name
        if s_name not in supplier_rekap:
            supplier_rekap[s_name] = {'total': 0, 'count': 0, 'items': []}
        supplier_rekap[s_name]['total'] += p.grand_total
        supplier_rekap[s_name]['count'] += 1
        supplier_rekap[s_name]['items'].append(p)

    # -----------------------------------------------
    # 4. LAPORAN STOK AKHIR
    # -----------------------------------------------
    stok_akhir_list = []
    total_nilai_hpp  = 0
    total_nilai_jual = 0
    for prod in products_all:
        stok  = prod.stock or 0
        hpp   = prod.hpp   or 0
        harga = prod.price or 0
        nilai_hpp  = stok * hpp
        nilai_jual = stok * harga
        total_nilai_hpp  += nilai_hpp
        total_nilai_jual += nilai_jual
        stok_akhir_list.append({
            'product':    prod,
            'stok':       stok,
            'hpp':        hpp,
            'harga_jual': harga,
            'nilai_hpp':  nilai_hpp,
            'nilai_jual': nilai_jual,
            'potensi_profit': nilai_jual - nilai_hpp,
        })

    context = {
        'page_title':    'Laporan',
        'date_from':     date_from.strftime('%Y-%m-%d'),
        'date_to':       (date_to - timedelta(days=1)).strftime('%Y-%m-%d'),
        'laba_rugi':     laba_rugi,
        'mutasi_list':   mutasi_list,
        'supplier_rekap': supplier_rekap,
        'stok_akhir_list': stok_akhir_list,
        'total_nilai_hpp':  total_nilai_hpp,
        'total_nilai_jual': total_nilai_jual,
        'total_potensi_profit': total_nilai_jual - total_nilai_hpp,
    }
    return render(request, 'posApp/reports.html', context)
