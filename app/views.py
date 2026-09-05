from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView ,DetailView,FormView
from django.contrib import messages
from .models import *
from .forms import *
import re
from .salary_utils import calculate_monthly_salary, summarize_monthly_salary
class CustomLoginView(LoginView):
    template_name = 'login.html'
    
    def get_success_url(self):
        user = self.request.user
        if user.is_authenticated:
            if user.role == 'manager':
                return reverse('app:manager_dashboard')
            elif user.role == 'accountant':
                return reverse('app:customer_list')
        return reverse('app:dashboard')  # fallback

    def form_valid(self, form):
        """If the form is valid, redirect to the success URL."""
        return super().form_valid(form)

def logout_view(request):
    logout(request)
    return redirect('app:login')

# Helper functions for role checks
def is_manager(user):
    return user.is_authenticated and user.role == 'manager'

def is_accountant(user):
    return user.is_authenticated and user.role == 'accountant'

@login_required
def dashboard(request):
    """Generic dashboard that redirects based on role."""
    if request.user.role == 'manager':
        return redirect('app:manager_dashboard')
    elif request.user.role == 'accountant':
        return redirect('app:accountant_dashboard')
    else:
        # fallback: show a generic page
        return render(request, 'dashboard.html', {'user': request.user})

@login_required
@user_passes_test(is_manager, login_url='app:dashboard')
def manager_dashboard(request):
    context = {
        'user': request.user,
        'can_manage_inventory': request.user.has_perm('app.can_manage_inventory'),
        'can_manage_sales': request.user.has_perm('app.can_manage_sales'),
        'can_view_financial_reports': request.user.has_perm('app.can_view_financial_reports'),
        'can_manage_employes': request.user.has_perm('app.can_manage_employes'),
    }
    return render(request, 'manager_dashboard.html', context)

@login_required
@user_passes_test(is_accountant, login_url='app:dashboard')
def accountant_dashboard(request):
    context = {
        'user': request.user,
        # Accountant may only view financial reports
        'can_view_financial_reports': request.user.has_perm('app.can_view_financial_reports'),
    }
    return render(request, 'accountant_dashboard.html', context)

from datetime import timedelta
from django.db.models import Q, Sum, Case, When, Value, IntegerField, F
from django.utils import timezone

class InventoryDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'inventory_dashboard.html'
    permission_required = 'app.can_manage_inventory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models import Category, Product, Supplier, BatchProduct, Unite

        # الإحصائيات الأساسية
        context['category_count'] = Category.objects.count()
        context['unite_count'] = Unite.objects.count()
        context['product_count'] = Product.objects.count()
        context['supplier_count'] = Supplier.objects.count()

        # ====== 1. المنتجات منخفضة المخزون ======
        low_stock_products = []
        for product in Product.objects.all():
            if product.total_quantity <= product.Count_Alarm:
                low_stock_products.append({
                    'name': product.name,
                    'quantity': product.total_quantity,
                    'alarm': product.Count_Alarm,
                    'id': product.id,
                })
        context['low_stock_products'] = low_stock_products
        context['low_stock_count'] = len(low_stock_products)

        # ====== 2. الدفعات المنتهية الصلاحية ======
        today = timezone.now().date()
        expired_batches = BatchProduct.objects.filter(
            expiration_date__lt=today
        ).select_related('product').order_by('expiration_date')
        context['expired_batches'] = expired_batches
        context['expired_count'] = expired_batches.count()

        # ====== 3. الدفعات التي ستنتهي خلال 30 يومًا ======
        soon_date = today + timedelta(days=30)
        soon_expiring_batches = BatchProduct.objects.filter(
            expiration_date__gte=today,
            expiration_date__lte=soon_date
        ).select_related('product').order_by('expiration_date')
        context['soon_expiring_batches'] = soon_expiring_batches
        context['soon_expiring_count'] = soon_expiring_batches.count()

        return context

class CategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Category
    paginate_by = 20
    template_name = 'category_list.html'
    context_object_name = 'categories'
    permission_required = 'app.can_manage_inventory'
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'category_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:category_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم إضافة الفئة بنجاح.')
        return response
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['name'].widget.attrs.update({'class': 'form-control'})
        form.fields['description'].widget.attrs.update({'class': 'form-control'})
        return form

class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Category
    fields = ['name', 'description']
    template_name = 'category_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:category_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث الفئة بنجاح.')
        return response

class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Category
    template_name = 'category_confirm_delete.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:category_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف الفئة بنجاح.')
        return super().delete(request, *args, **kwargs)


class UniteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Unite
    template_name = 'unite_list.html'
    context_object_name = 'unites'
    permission_required = 'app.can_manage_inventory'
    ordering = ['name']
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) )
        return queryset

class UniteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Unite
    fields = ['name']
    template_name = 'unite_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:unite_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم إضافة الوحدة بنجاح.')
        return response

class UniteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Unite
    fields = ['name']
    template_name = 'unite_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:unite_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث الوحدة بنجاح.')
        return response

class UniteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Unite
    template_name = 'unite_confirm_delete.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:unite_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف الوحدة بنجاح.')
        return super().delete(request, *args, **kwargs)


# --- Product CRUD Views ---

from django.shortcuts import get_object_or_404
from django.db.models import Q

class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    permission_required = 'app.can_manage_inventory'
    ordering = ['name']
    paginate_by = 20  # optional

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(barcode__icontains=search)
            )
        return queryset

class ProductDetailByBarcodeView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'
    permission_required = 'app.can_manage_inventory'

    def get_object(self, queryset=None):
        barcode = self.kwargs.get('barcode')
        return get_object_or_404(Product, barcode=barcode)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add total quantity and batch info if needed
        context['total_quantity'] = self.object.total_quantity
        context['batches'] = self.object.batches.all().order_by('expiration_date')
        return context

class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Product
    fields = ['image','name', 'category', 'unite', 'barcode', 'sale_price', 'sale_priceAmount', 'Pakage', 'Count_Alarm']
    template_name = 'product_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:product_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add Bootstrap classes to all fields
        for field_name, field in form.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم إضافة المنتج بنجاح.')
        return response

class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Product
    fields = ['image','name', 'category', 'unite', 'barcode', 'sale_price', 'sale_priceAmount', 'Pakage', 'Count_Alarm']
    template_name = 'product_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:product_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field_name, field in form.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث المنتج بنجاح.')
        return response

class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Product
    template_name = 'product_confirm_delete.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:product_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف المنتج بنجاح.')
        return super().delete(request, *args, **kwargs)

import barcode
from barcode.writer import ImageWriter
from io import BytesIO
from django.http import HttpResponse

def barcode_image(request, barcode):
    # Generate barcode image
    ean = barcode.get_barcode_class('ean13')
    ean_obj = ean(barcode, writer=ImageWriter())
    buffer = BytesIO()
    ean_obj.write(buffer)
    return HttpResponse(buffer.getvalue(), content_type='image/png')

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required, permission_required
from .models import Product

@login_required
def check_barcode(request):
    barcode = request.GET.get('barcode')
    if not barcode:
        return JsonResponse({'exists': False})
    try:
        product = Product.objects.get(barcode=barcode)
        return JsonResponse({'exists': True, 'product_name': product.name})
    except Product.DoesNotExist:
        return JsonResponse({'exists': False})


class ExchangeRateListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ExchangeRate
    template_name = 'exchange_rate_list.html'
    context_object_name = 'rates'
    permission_required = 'app.can_manage_inventory'  # غير حسب الحاجة
    ordering = ['-date']  # الأحدث أولاً
    paginate_by = 20

class ExchangeRateCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ExchangeRate
    fields = ['rate']  # date يتم تعبئته تلقائياً
    template_name = 'exchange_rate_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:exchange_rate_list')

    def form_valid(self, form):
        # إذا أردت منع تكرار التاريخ لنفس اليوم (اختياري)
        # يمكنك التحقق هنا
        response = super().form_valid(form)
        messages.success(self.request, 'تم إضافة سعر الصرف بنجاح.')
        return response

class ExchangeRateUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ExchangeRate
    fields = ['rate']
    template_name = 'exchange_rate_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:exchange_rate_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث سعر الصرف بنجاح.')
        return response

class ExchangeRateDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ExchangeRate
    template_name = 'exchange_rate_confirm_delete.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:exchange_rate_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف سعر الصرف بنجاح.')
        return super().delete(request, *args, **kwargs)


class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customer_list.html'
    context_object_name = 'customers'
  
    ordering = ['name']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model = Customer
    fields = ['name', 'phone', 'email', 'address']
    template_name = 'customer_form.html'

    success_url = reverse_lazy('app:customer_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم إضافة العميل بنجاح.')
        return response

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    fields = ['name', 'phone', 'email', 'address']
    template_name = 'customer_form.html'
  
    success_url = reverse_lazy('app:customer_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث بيانات العميل بنجاح.')
        return response

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'customer_confirm_delete.html'
  
    success_url = reverse_lazy('app:customer_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف العميل بنجاح.')
        return super().delete(request, *args, **kwargs)

# <li class="nav-item">
#     <a class="nav-link {% if 'customer' in request.resolver_match.url_name %}active{% endif %}" href="{% url 'app:customer_list' %}">
#         <i class="fas fa-users"></i> العملاء
#     </a>
# </li>


class SupplierListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Supplier
    template_name = 'supplier_list.html'
    context_object_name = 'suppliers'
    permission_required = 'app.can_manage_inventory'  # أو can_manage_purchases
    ordering = ['name']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset

class SupplierCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Supplier
    fields = ['name', 'phone', 'email', 'address']
    template_name = 'supplier_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:supplier_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم إضافة المورد بنجاح.')
        return response

class SupplierUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Supplier
    fields = ['name', 'phone', 'email', 'address']
    template_name = 'supplier_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:supplier_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث بيانات المورد بنجاح.')
        return response

class SupplierDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'supplier_confirm_delete.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:supplier_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف المورد بنجاح.')
        return super().delete(request, *args, **kwargs)


class PurchaseInvoiceListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = PurchaseInvoice
    template_name = 'purchase_invoice_list.html'
    context_object_name = 'invoices'
    permission_required = 'app.can_manage_inventory'  # أو can_manage_inventory
    ordering = ['-date']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search) |
                Q(supplier__name__icontains=search)
            )
        return queryset

class PurchaseInvoiceCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PurchaseInvoice
    form_class = PurchaseInvoiceForm
    template_name = 'purchase_invoice_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:purchase_invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = BatchProductFormSet(self.request.POST)
        else:
            context['formset'] = BatchProductFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, 'تم إضافة فاتورة الشراء بنجاح.')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

class PurchaseInvoiceUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PurchaseInvoice
    form_class = PurchaseInvoiceForm
    template_name = 'purchase_invoice_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:purchase_invoice_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = BatchProductFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = BatchProductFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            messages.success(self.request, 'تم تحديث فاتورة الشراء بنجاح.')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

class PurchaseInvoiceDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = PurchaseInvoice
    template_name = 'purchase_invoice_confirm_delete.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:purchase_invoice_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف فاتورة الشراء بنجاح.')
        return super().delete(request, *args, **kwargs)

from django.views import View

class ProductByBarcodeView(LoginRequiredMixin, View):
    def get(self, request):
        barcode = request.GET.get('barcode', '').strip()
        if not barcode:
            return JsonResponse({'exists': False, 'barcode': ''})

        try:
            product = Product.objects.get(barcode=barcode)
            last_batch = product.batches.order_by('-created_at').first()
            purchase_price = last_batch.purchase_price if last_batch else 0
            return JsonResponse({
                'exists': True,
                'product_id': product.id,
                'product_name': product.name,
                'purchase_price': float(purchase_price) if purchase_price else 0,
                'barcode': barcode
            })
        except Product.DoesNotExist:
            return JsonResponse({
                'exists': False,
                'barcode': barcode
            })

class GenerateInvoiceNumberView(LoginRequiredMixin, View):
    def get(self, request):
        new_number = PurchaseInvoice.generate_invoice_number()
        return JsonResponse({'invoice_number': new_number})


class PaymentPurchaseListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = PaymentPurchase
    template_name = 'payment_purchase_list.html'
    context_object_name = 'payments'
    permission_required = 'app.can_manage_inventory'  # أو can_manage_inventory
    ordering = ['-date']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(invoice_id__invoice_number__icontains=search) |
                Q(invoice_id__supplier__name__icontains=search) |
                Q(amount__icontains=search) |
                Q(method__icontains=search)
            )
        return queryset

class PaymentPurchaseCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = PaymentPurchase
    fields = ['Supplier_id','amountSA', 'amountDollar', 'method', 'exchange_rate_used', 'notes']
    template_name = 'payment_purchase_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:payment_purchase_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم إضافة دفعة الشراء بنجاح.')
        return response

class PaymentPurchaseUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = PaymentPurchase
    fields = ['Supplier_id','amountSA','amountDollar', 'method', 'exchange_rate_used', 'notes']
    template_name = 'payment_purchase_form.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:payment_purchase_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث دفعة الشراء بنجاح.')
        return response

class PaymentPurchaseDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = PaymentPurchase
    template_name = 'payment_purchase_confirm_delete.html'
    permission_required = 'app.can_manage_inventory'
    success_url = reverse_lazy('app:payment_purchase_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف دفعة الشراء بنجاح.')
        return super().delete(request, *args, **kwargs)



class HRDashboardView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'hr_dashboard.html'
    permission_required = 'app.can_manage_employes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # إحصائيات الموظفين
        context['total_employees'] = Employee.objects.count()
        context['active_employees'] = Employee.objects.filter(is_active=True).count()
        context['inactive_employees'] = Employee.objects.filter(is_active=False).count()
        # إجمالي التكاليف (إذا كان لديك حقل amount في نموذج Cost)
        from django.db.models import Sum
        total_cost = Cost.objects.aggregate(total=Sum('amount'))['total']
        context['total_costs'] = total_cost if total_cost else 0
        # آخر 5 موظفين
        context['recent_employees'] = Employee.objects.order_by('-created_at')[:5]
        return context

class EmployeeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Employee
    template_name = 'employee_list.html'
    context_object_name = 'employees'
    permission_required = 'app.can_manage_employes'
    paginate_by = 20
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # البحث
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(position__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        
        # فلترة حسب الحالة (نشط / غير نشط)
        is_active = self.request.GET.get('is_active')
        if is_active in ['0', '1']:
            queryset = queryset.filter(is_active=(is_active == '1'))
        
        return queryset


class EmployeeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Employee
    template_name = 'employee_list.html'
    context_object_name = 'employees'
    permission_required = 'app.can_manage_employes'
    paginate_by = 20
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(position__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        is_active = self.request.GET.get('is_active')
        if is_active in ['0', '1']:
            queryset = queryset.filter(is_active=(is_active == '1'))
        return queryset


class EmployeeCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Employee
    form_class = EmployeeForm  # استخدام النموذج المخصص بدلاً من fields
    template_name = 'employee_form.html'
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'إضافة موظف جديد'
        context['submit_text'] = 'إضافة'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'تم إضافة الموظف بنجاح.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'حدث خطأ في إدخال البيانات. يرجى التحقق من الحقول.')
        return super().form_invalid(form)


class EmployeeUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm  # استخدام النموذج المخصص أيضاً
    template_name = 'employee_form.html'
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'تعديل بيانات الموظف'
        context['submit_text'] = 'تحديث'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث بيانات الموظف بنجاح.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'حدث خطأ في تحديث البيانات. يرجى التحقق من الحقول.')
        return super().form_invalid(form)

class EmployeeDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Employee
    template_name = 'employee_confirm_delete.html'
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:employee_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف الموظف بنجاح.')
        return super().delete(request, *args, **kwargs)




# قائمة المستخدمين
class UserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = User
    template_name = 'user_list.html'
    context_object_name = 'users'
    permission_required = 'app.can_manage_employes'  # أو صلاحية مخصصة للمستخدمين
    ordering = ['username']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
            )
        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)
        return queryset

# إضافة مستخدم
class UserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'user_form.html'
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم إضافة المستخدم بنجاح.')
        return response

# تعديل مستخدم
class UserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = User
    form_class = CustomUserChangeForm
    template_name = 'user_form.html'
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'تم تحديث بيانات المستخدم بنجاح.')
        return response

# حذف مستخدم
class UserDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = User
    template_name = 'user_confirm_delete.html'
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:user_list')

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'تم حذف المستخدم بنجاح.')
        return super().delete(request, *args, **kwargs)

# تغيير كلمة المرور
class UserChangePasswordView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'user_change_password.html'
    form_class = CustomPasswordChangeForm
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:user_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, 'تم تغيير كلمة المرور بنجاح.')
        return super().form_valid(form)


class ActionMoneyFullAllListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ActionMoney_FullAll
    template_name = 'allowance_list.html'
    context_object_name = 'allowances'
    permission_required = 'app.can_manage_employes'
    paginate_by = 20

    def get_queryset(self):
        self.employee = get_object_or_404(Employee, pk=self.kwargs['employee_id'])
        return ActionMoney_FullAll.objects.filter(Employee=self.employee)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context

class ActionMoneyFullAllCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = ActionMoney_FullAll

    form_class = ActionMoneyFullAllForm     
    template_name = 'allowance_form.html'
    permission_required = 'app.can_manage_employes'

    def get_initial(self):
        initial = super().get_initial()
        self.employee = get_object_or_404(Employee, pk=self.kwargs['employee_id'])
        initial['Employee'] = self.employee
        return initial
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context
    def form_valid(self, form):
        form.instance.Employee = self.employee
        messages.success(self.request, 'تم إضافة العلاوة/العقوبة بنجاح.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:allowance_list', kwargs={'employee_id': self.employee.pk})

class ActionMoneyFullAllUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = ActionMoney_FullAll
    form_class = ActionMoneyFullAllForm 
    template_name = 'allowance_form.html'
    permission_required = 'app.can_manage_employes'

    def get_success_url(self):
        return reverse_lazy('app:allowance_list', kwargs={'employee_id': self.object.Employee.pk})

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث العلاوة/العقوبة بنجاح.')
        return super().form_valid(form)

class ActionMoneyFullAllDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = ActionMoney_FullAll
    template_name = 'allowance_confirm_delete.html'
    permission_required = 'app.can_manage_employes'

    def get_success_url(self):
        return reverse_lazy('app:allowance_list', kwargs={'employee_id': self.object.Employee.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف العلاوة/العقوبة بنجاح.')
        return super().delete(request, *args, **kwargs)


class SalaryPaymentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SalaryPayment
    template_name = 'salary_payment_list.html'
    context_object_name = 'payments'
    permission_required = 'app.can_manage_employes'
    paginate_by = 20

    def get_queryset(self):
        self.employee = get_object_or_404(Employee, pk=self.kwargs['employee_id'])
        return SalaryPayment.objects.filter(Employee=self.employee).order_by('-payment_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        total_paid = self.get_queryset().aggregate(total=models.Sum('amount'))['total'] or 0
        context['total_paid'] = total_paid
        return context

class SalaryPaymentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = SalaryPayment
    form_class = SalaryPaymentForm  
    template_name = 'salary_payment_form.html'
    permission_required = 'app.can_manage_employes'

    def dispatch(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, pk=self.kwargs['employee_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context

    def form_valid(self, form):
        form.instance.Employee = self.employee
        # payment_date is auto_now_add, so not in form
        messages.success(self.request, 'تم إضافة سند الصرف بنجاح.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:salary_payment_list', kwargs={'employee_id': self.employee.pk})

class SalaryPaymentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = SalaryPayment
    form_class = SalaryPaymentForm
    template_name = 'salary_payment_form.html'
    permission_required = 'app.can_manage_employes'

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث سند الصرف بنجاح.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:salary_payment_list', kwargs={'employee_id': self.object.Employee.pk})

class SalaryPaymentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = SalaryPayment
    template_name = 'salary_payment_confirm_delete.html'
    permission_required = 'app.can_manage_employes'

    def get_success_url(self):
        return reverse_lazy('app:salary_payment_list', kwargs={'employee_id': self.object.Employee.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف سند الصرف بنجاح.')
        return super().delete(request, *args, **kwargs)


class ActionMoneyMonthListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Action_Money_Month
    template_name = 'monthly_action_list.html'
    context_object_name = 'actions'
    permission_required = 'app.can_manage_employes'
    paginate_by = 20

    def get_queryset(self):
        self.employee = get_object_or_404(Employee, pk=self.kwargs['employee_id'])
        return Action_Money_Month.objects.filter(Employee=self.employee).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        actions = self.get_queryset()
        total_bonus = actions.filter(relationship='Bonus').aggregate(total=models.Sum('amount'))['total'] or 0
        total_advance = actions.filter(relationship='advance').aggregate(total=models.Sum('amount'))['total'] or 0
        total_deduction = actions.filter(relationship='Deduction').aggregate(total=models.Sum('amount'))['total'] or 0
        context['total_bonus'] = total_bonus
        context['total_advance'] = total_advance
        context['total_deduction'] = total_deduction
        context['net'] = total_bonus - total_advance - total_deduction
        return context

class ActionMoneyMonthCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Action_Money_Month
    fields = ['relationship', 'description', 'amount']
    template_name = 'monthly_action_form.html'
    permission_required = 'app.can_manage_employes'

    def dispatch(self, request, *args, **kwargs):
        self.employee = get_object_or_404(Employee, pk=self.kwargs['employee_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee'] = self.employee
        return context

    def form_valid(self, form):
        form.instance.Employee = self.employee
        messages.success(self.request, 'تم إضافة المكافأة/السلفة/الخصم بنجاح.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:monthly_action_list', kwargs={'employee_id': self.employee.pk})

class ActionMoneyMonthUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Action_Money_Month
    fields = ['relationship', 'description', 'amount']
    template_name = 'monthly_action_form.html'
    permission_required = 'app.can_manage_employes'

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث المكافأة/السلفة/الخصم بنجاح.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:monthly_action_list', kwargs={'employee_id': self.object.Employee.pk})

class ActionMoneyMonthDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Action_Money_Month
    template_name = 'monthly_action_confirm_delete.html'
    permission_required = 'app.can_manage_employes'

    def get_success_url(self):
        return reverse_lazy('app:monthly_action_list', kwargs={'employee_id': self.object.Employee.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف المكافأة/السلفة/الخصم بنجاح.')
        return super().delete(request, *args, **kwargs)


class EmployeeSalaryReportView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'employee_salary_report.html'
    permission_required = 'app.can_manage_employes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        employee = get_object_or_404(Employee, pk=self.kwargs['employee_id'])
        context['employee'] = employee

        # قراءة المعاملات من الرابط
        up_to_date_str = self.request.GET.get('up_to_date')
        up_to_date = None
        if up_to_date_str:
            try:
                up_to_date = datetime.strptime(up_to_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        if not up_to_date:
            up_to_date = timezone.now().date()

        advance_installments = self.request.GET.get('advance_installments', '1')
        try:
            advance_installments = int(advance_installments)
            if advance_installments < 1:
                advance_installments = 1
        except ValueError:
            advance_installments = 1

        context['up_to_date'] = up_to_date
        context['advance_installments'] = advance_installments

        # حساب الراتب
        monthly_data = calculate_monthly_salary(employee, up_to_date, advance_installments)
        summary = summarize_monthly_salary(employee, up_to_date, advance_installments)
        context['monthly_data'] = monthly_data
        context['summary'] = summary

        return context

class SupplierAccountView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Supplier
    template_name = 'supplier_account.html'
    context_object_name = 'supplier'
    permission_required = 'app.can_manage_inventory'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.object

        # جميع فواتير الشراء لهذا المورد
        invoices = PurchaseInvoice.objects.filter(supplier=supplier).order_by('-date')

        # جميع المدفوعات لهذا المورد (مباشرة من حقل Supplier_id)
        payments = PaymentPurchase.objects.filter(Supplier_id=supplier).order_by('-date')

        invoice_data = []
        total_purchases = 0
        for inv in invoices:
            total = inv.details.aggregate(
                total=Sum(F('quantity') * F('purchase_price'))
            )['total'] or 0
            total_purchases += total

            invoice_data.append({
                'invoice': inv,
                'total': total,
                'balance': total,  # الرصيد المتبقي = إجمالي الفاتورة (لأن الدفعات غير مرتبطة)
            })

        # إجمالي المدفوعات بالدولار والسوري
        total_payments = payments.aggregate(total=Sum('amountDollar'))['total'] or 0
        total_payments_sa = payments.aggregate(total=Sum('amountSA'))['total'] or 0

        balance = total_purchases - total_payments

        if balance > 0:
            balance_type = 'دائن'
        elif balance < 0:
            balance_type = 'مدين'
        else:
            balance_type = 'متساوي'

        context['invoice_data'] = invoice_data
        context['payments'] = payments
        context['total_purchases'] = total_purchases
        context['total_payments'] = total_payments
        context['total_payments_sa'] = total_payments_sa  # إضافة المبلغ بالسوري
        context['balance'] = balance
        context['balance_type'] = balance_type

        return context

class CostCategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = CostCategory
    template_name = 'cost_category_list.html'
    context_object_name = 'categories'
    permission_required = 'app.can_manage_employes'
    paginate_by = 20
    ordering = ['name']

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        return queryset

class CostCategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = CostCategory
    fields = ['name', 'description']
    template_name = 'cost_category_form.html'
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:cost_category_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        messages.success(self.request, 'تم إضافة فئة التكلفة بنجاح.')
        return super().form_valid(form)

class CostCategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = CostCategory
    fields = ['name', 'description']
    template_name = 'cost_category_form.html'
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:cost_category_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث فئة التكلفة بنجاح.')
        return super().form_valid(form)

class CostCategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = CostCategory
    template_name = 'cost_category_confirm_delete.html'
    permission_required = 'app.can_manage_employes'
    success_url = reverse_lazy('app:cost_category_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف فئة التكلفة بنجاح.')
        return super().delete(request, *args, **kwargs)



class CostListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cost
    template_name = 'cost_list.html'
    context_object_name = 'costs'
    permission_required = 'app.can_manage_employes'
    paginate_by = 20

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(CostCategory, pk=self.kwargs['category_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Cost.objects.filter(category=self.category).order_by('-date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        total = self.get_queryset().aggregate(total=Sum('amount'))['total'] or 0
        context['total_amount'] = total
        return context

from django import forms
from django.utils import timezone

class CostCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Cost
    fields = ['amount', 'date', 'description']
    template_name = 'cost_form.html'
    permission_required = 'app.can_manage_employes'

    def dispatch(self, request, *args, **kwargs):
        self.category = get_object_or_404(CostCategory, pk=self.kwargs['category_id'])
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        initial['date'] = timezone.now().date()  # تاريخ اليوم كقيمة افتراضية
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # تعيين الـ widget لحقل التاريخ
        form.fields['date'].widget = forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        )
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

    def form_valid(self, form):
        form.instance.category = self.category
        messages.success(self.request, 'تم إضافة التكلفة بنجاح.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:cost_list', kwargs={'category_id': self.category.pk})


class CostUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Cost
    fields = ['amount', 'date', 'description']
    template_name = 'cost_form.html'
    permission_required = 'app.can_manage_employes'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # تعيين الـ widget لحقل التاريخ
        form.fields['date'].widget = forms.DateInput(
            attrs={'class': 'form-control', 'type': 'date'}
        )
        return form

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث التكلفة بنجاح.')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('app:cost_list', kwargs={'category_id': self.object.category.pk})


class CostDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Cost
    template_name = 'cost_confirm_delete.html'
    permission_required = 'app.can_manage_employes'

    def get_success_url(self):
        return reverse_lazy('app:cost_list', kwargs={'category_id': self.object.category.pk})

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف التكلفة بنجاح.')
        return super().delete(request, *args, **kwargs)


import json
from django.core.serializers.json import DjangoJSONEncoder
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db import transaction
from django.forms import inlineformset_factory
from django.utils import timezone
from django.contrib import messages
from .models import SalesInvoice, SalesInvoiceDetail, BatchProduct, Product
from .forms import SalesInvoiceForm, SalesInvoiceDetailForm

SalesInvoiceDetailFormSet = inlineformset_factory(
    SalesInvoice,
    SalesInvoiceDetail,
    form=SalesInvoiceDetailForm,
    extra=1,
    can_delete=True,
)

from django.views.generic.edit import CreateView
from .models import SalesInvoice
from .forms import SalesInvoiceForm, SalesInvoiceDetailFormSet

class SalesInvoiceCreateView(CreateView):
    model = SalesInvoice
    form_class = SalesInvoiceForm
    template_name = 'sales_invoice_create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['detail_formset'] = SalesInvoiceDetailFormSet(self.request.POST)
        else:
            context['detail_formset'] = SalesInvoiceDetailFormSet()
        # تمرير المنتجات
        context['products'] = Product.objects.all()
        return context

def generate_invoice_number():
    """توليد رقم فاتورة فريد على شكل INV-YYYY-MM-XXXX"""
    today = timezone.now()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    # العد للشهر الحالي
    last_invoice = SalesInvoice.objects.filter(
        date__year=today.year,
        date__month=today.month
    ).order_by('-id').first()
    
    if last_invoice:
        try:
            # استخراج الرقم التسلسلي من آخر فاتورة (الجزء الأخير بعد آخر -)
            parts = last_invoice.invoice_number.split('-')
            last_number = int(parts[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    else:
        new_number = 1
    
    return f"INV-{year}-{month}-{new_number:04d}"

@login_required
def sales_invoice_create(request):
    if request.method == 'POST':
        form = SalesInvoiceForm(request.POST)
        formset = SalesInvoiceDetailFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                invoice = form.save(commit=False)
                # إذا كان رقم الفاتورة فارغاً، نولده تلقائياً
                if not invoice.invoice_number or invoice.invoice_number.strip() == '':
                    invoice.invoice_number = generate_invoice_number()
                invoice.save()
                
                # حفظ التفاصيل
                details = formset.save(commit=False)
                for detail in details:
                    detail.invoice = invoice
                    detail.create_by = request.user
                    detail.save()
                # حذف التفاصيل المحذوفة (إذا كان formset يسمح بذلك)
                for deleted in formset.deleted_objects:
                    deleted.delete()
                
                return redirect('app:invoice_detail', pk=invoice.pk)  # تأكد من وجود هذا الرابط
    else:
        # توليد رقم فاتورة مبدئي لعرضه في النموذج
        initial_number = generate_invoice_number()
        form = SalesInvoiceForm(initial={'invoice_number': initial_number})
        formset = SalesInvoiceDetailFormSet()

    context = {
        'form': form,
        'detail_formset': formset,
        'products': Product.objects.all(),
        'exchange_rates': ExchangeRate.objects.all(),
    }
    return render(request, 'sales_invoice_create.html', context)


def get_product_price(request):
    product_id = request.GET.get('product_id')
    is_package = request.GET.get('is_package') == 'true'
    if product_id:
        try:
            product = Product.objects.get(pk=product_id)
            price = product.sale_priceAmount if is_package else product.sale_price
            # استخدام الخاصية total_quantity لحساب الكمية المتاحة
            available = product.total_quantity
            return JsonResponse({
                'price': float(price),
                'available': available
            })
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
    return JsonResponse({'error': 'Missing product_id'}, status=400)

from django.views.generic import DetailView
from .models import SalesInvoice

class SalesInvoiceDetailView(DetailView):
    model = SalesInvoice
    template_name = 'sales_invoice_detail.html'
    context_object_name = 'invoice'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.object
        
        # جلب التفاصيل مع حساب subtotal لكل تفصيلة
        details = invoice.details.all()
        for detail in details:
            detail.subtotal = detail.quantity * detail.price  # إضافة خاصية subtotal
        
        # حساب الإجماليات
        total_usd = sum(detail.subtotal for detail in details)
        rate = invoice.exchange_rate.rate if invoice.exchange_rate else 0
        discount = invoice.Discount or 0
        net_usd = total_usd - discount
        
        context['details'] = details
        context['total_usd'] = total_usd
        context['total_syp'] = total_usd * rate
        context['net_usd'] = net_usd
        context['net_syp'] = net_usd * rate
        context['rate'] = rate
        context['created_by'] = details.first().create_by.username if details.exists() else 'غير معروف'
        
        return context 

from django.views.generic import ListView
from django.db.models import Sum, F, DecimalField, Q
from django.shortcuts import render
from .models import SalesInvoice, SalesInvoiceDetail

class SalesInvoiceListView(ListView):
    model = SalesInvoice
    template_name = 'sales_invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20  # عدد الفواتير في كل صفحة
    ordering = ['-date']  # الترتيب الافتراضي (الأحدث أولاً)

    def get_queryset(self):
        queryset = super().get_queryset()
        # حساب إجمالي المبلغ لكل فاتورة (مجموع quantity * price لكل تفصيلة)
        queryset = queryset.annotate(
            total_amount=Sum(
                F('details__quantity') * F('details__price'),
                output_field=DecimalField(max_digits=12, decimal_places=2)
            )
        ).order_by('-date')

        # معالجة البحث (اختياري)
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(invoice_number__icontains=search_query) |
                Q(customer__name__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # إضافة قيمة البحث إلى السياق للحفاظ عليها في القالب
        context['search_query'] = self.request.GET.get('q', '')
        return context

from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.http import JsonResponse
import json
from .models import SalesInvoice, SalesInvoiceDetail, Product
from .forms import SalesInvoiceForm

class SalesInvoiceUpdateView(LoginRequiredMixin, UpdateView):
    model = SalesInvoice
    form_class = SalesInvoiceForm
    template_name = 'sales_invoice_edit.html'
    context_object_name = 'invoice'
    success_url = '/app/sales-invoices/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = self.object
        context['existing_details'] = invoice.details.all()
        context['products'] = Product.objects.all()
        context['exchange_rates'] = ExchangeRate.objects.all()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        # حفظ بيانات الفاتورة الأساسية
        invoice = form.save(commit=False)
        invoice.save()

        # معالجة التفاصيل من POST
        # حذف التفاصيل التي تم وضع علامة حذف عليها
        deleted_details = self.request.POST.get('deleted_details')
        if deleted_details:
            try:
                deleted_ids = json.loads(deleted_details)
                SalesInvoiceDetail.objects.filter(id__in=deleted_ids, invoice=invoice).delete()
            except:
                pass

        # تحديث أو إنشاء التفاصيل
        # البحث عن جميع مفاتيح التفاصيل في POST
        detail_keys = [key for key in self.request.POST.keys() if key.startswith('details-') and key.endswith('-product')]
        indices = set()
        for key in detail_keys:
            parts = key.split('-')
            if len(parts) >= 3:
                try:
                    idx = int(parts[1])
                    indices.add(idx)
                except ValueError:
                    pass

        for idx in indices:
            product_id = self.request.POST.get(f'details-{idx}-product')
            quantity = self.request.POST.get(f'details-{idx}-quantity')
            price = self.request.POST.get(f'details-{idx}-price')
            is_package = self.request.POST.get(f'details-{idx}-Is_package', 'off') == 'on'
            detail_id = self.request.POST.get(f'details-{idx}-id')

            if product_id and quantity and price:
                try:
                    product = Product.objects.get(pk=product_id)
                    if detail_id:
                        # تحديث تفصيلة موجودة
                        detail = SalesInvoiceDetail.objects.get(pk=detail_id, invoice=invoice)
                        detail.product = product
                        detail.quantity = int(quantity)
                        detail.price = float(price)
                        detail.Is_package = is_package
                        detail.save()
                    else:
                        # إنشاء تفصيلة جديدة
                        detail = SalesInvoiceDetail(
                            invoice=invoice,
                            product=product,
                            quantity=int(quantity),
                            price=float(price),
                            Is_package=is_package,
                            create_by=self.request.user
                        )
                        detail.save()
                except (Product.DoesNotExist, SalesInvoiceDetail.DoesNotExist, ValueError):
                    pass

        return redirect('app:invoice_detail', pk=invoice.pk)
class SalesInvoiceDeleteView(LoginRequiredMixin, DeleteView):
    model = SalesInvoice
    template_name = 'sales_invoice_confirm_delete.html'
    context_object_name = 'invoice'
    success_url = reverse_lazy('app:sales_invoice_list')

class PaymentSalesListView(LoginRequiredMixin, ListView):
    model = PaymentSales
    template_name = 'payment_sales_list.html'
    context_object_name = 'payments'
    ordering = ['-date']
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        # فلترة حسب رقم الفاتورة إذا ورد في الطلب
        invoice = self.request.GET.get('invoice')
        if invoice:
            queryset = queryset.filter(invoice_id__invoice_number__icontains=invoice)
        return queryset

class PaymentSalesCreateView(LoginRequiredMixin, CreateView):
    model = PaymentSales
    form_class = PaymentSalesForm
    template_name = 'payment_sales_form.html'
    success_url = reverse_lazy('app:payment_sales_list')

    def form_valid(self, form):
        form.instance.create_by = self.request.user
        messages.success(self.request, 'تم إضافة دفعة المبيعات بنجاح.')
        return super().form_valid(form)

class PaymentSalesUpdateView(LoginRequiredMixin, UpdateView):
    model = PaymentSales
    form_class = PaymentSalesForm
    template_name = 'payment_sales_form.html'
    success_url = reverse_lazy('app:payment_sales_list')

    def form_valid(self, form):
        messages.success(self.request, 'تم تحديث دفعة المبيعات بنجاح.')
        return super().form_valid(form)

class PaymentSalesDeleteView(LoginRequiredMixin, DeleteView):
    model = PaymentSales
    template_name = 'payment_sales_confirm_delete.html'
    success_url = reverse_lazy('app:payment_sales_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'تم حذف دفعة المبيعات بنجاح.')
        return super().delete(request, *args, **kwargs)

# views.py
from django.http import JsonResponse
from .models import Product

def product_data(request, product_id):
    try:
        product = Product.objects.get(pk=product_id)
        data = {
            'exists': True,
            'sale_price': float(product.sale_price),
            'sale_priceAmount': float(product.sale_priceAmount),
            'product_name': product.name,
        }
    except Product.DoesNotExist:
        data = {'exists': False}
    return JsonResponse(data)

# views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model
from .emails import send_password_reset_email

User = get_user_model()

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            messages.error(request, 'الرجاء إدخال البريد الإلكتروني.')
            return render(request, 'password_reset_request.html')

        # محاولة إرسال البريد
        success = send_password_reset_email(email)
        if success:
            messages.success(request, 'تم إرسال كلمة المرور الجديدة إلى بريدك الإلكتروني.')
            return redirect('app:login')
        else:
            messages.error(request, 'هذا البريد الإلكتروني غير مسجل في النظام.')
            return render(request, 'password_reset_request.html')

    return render(request, 'password_reset_request.html')

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum, F, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    PurchaseInvoice, BatchProduct, SalesInvoice, SalesInvoiceDetail,
    PaymentPurchase, PaymentSales, Cost, SalaryPayment
)


class FinancialReportView(LoginRequiredMixin, TemplateView):
    template_name = 'financial_statistics.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ====== قراءة معاملات الفلتر ======
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # تعيين التواريخ الافتراضية (آخر 30 يوماً)
        if not start_date:
            start_date = (timezone.now() - timedelta(days=30)).date()
        else:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = (timezone.now() - timedelta(days=30)).date()

        if not end_date:
            end_date = timezone.now().date()
        else:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            except ValueError:
                end_date = timezone.now().date()

        # التأكد من أن start_date <= end_date
        if start_date > end_date:
            start_date, end_date = end_date, start_date

        context['start_date'] = start_date.strftime('%Y-%m-%d')
        context['end_date'] = end_date.strftime('%Y-%m-%d')

        # ====== 1. إجمالي فواتير الشراء (من الدفعات) ======
        # حساب إجمالي المشتريات من BatchProduct المرتبطة بفواتير الشراء في الفترة
        total_purchases = BatchProduct.objects.filter(
            invoice__date__gte=start_date,
            invoice__date__lte=end_date
        ).aggregate(
            total=Sum(F('quantity') * F('purchase_price'))
        )['total'] or 0

        # ====== 2. إجمالي فواتير البيع (من التفاصيل) ======
        total_sales = SalesInvoiceDetail.objects.filter(
            invoice__date__gte=start_date,
            invoice__date__lte=end_date
        ).aggregate(
            total=Sum(F('quantity') * F('price'))
        )['total'] or 0

        # ====== 3. إجمالي مدفوعات المشتريات (للموردين) ======
        total_payment_purchases = PaymentPurchase.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(
            total=Sum('amountDollar')
        )['total'] or 0

        # ====== 4. إجمالي مدفوعات المبيعات (من العملاء) ======
        total_payment_sales = PaymentSales.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(
            total=Sum('amountDollar')
        )['total'] or 0

        # ====== 5. إجمالي التكاليف التشغيلية ======
        total_costs = Cost.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # ====== 6. إجمالي سندات صرف الرواتب ======
        total_salaries = SalaryPayment.objects.filter(
            payment_date__gte=start_date,
            payment_date__lte=end_date
        ).aggregate(
            total=Sum('amount')
        )['total'] or 0

        # ====== معالجة الأرقام ======
        # تحويل الكل إلى float للحسابات
        total_purchases = float(total_purchases)
        total_sales = float(total_sales)
        total_payment_purchases = float(total_payment_purchases)
        total_payment_sales = float(total_payment_sales)
        total_costs = float(total_costs)
        total_salaries = float(total_salaries)

        # ====== حساب الدائن والمدين ======
        # الجانب المدين (Debit) - الأصول والمصروفات
        debit_side = {
            'sales': total_sales,          # المبيعات (إيراد)
            'costs': total_costs,          # التكاليف (مصروف)
            'salaries': total_salaries,    # الرواتب (مصروف)
        }
        total_debit = sum(debit_side.values())

        # الجانب الدائن (Credit) - الخصوم والإيرادات المؤجلة / التزامات
        credit_side = {
            'purchases': total_purchases,              # المشتريات (مخزون / موردين)
            'payment_purchases': total_payment_purchases,  # مدفوعات للموردين
            'payment_sales': total_payment_sales,          # مقبوضات من العملاء
        }
        total_credit = sum(credit_side.values())

        # ====== الرصيد النهائي ======
        balance = total_debit - total_credit

        # ====== السياق النهائي ======
        context['total_purchases'] = total_purchases
        context['total_sales'] = total_sales
        context['total_payment_purchases'] = total_payment_purchases
        context['total_payment_sales'] = total_payment_sales
        context['total_costs'] = total_costs
        context['total_salaries'] = total_salaries

        context['debit_side'] = debit_side
        context['credit_side'] = credit_side
        context['total_debit'] = total_debit
        context['total_credit'] = total_credit
        context['balance'] = balance

        # نوع الرصيد
        if balance > 0:
            context['balance_type'] = 'مدين (ربح / أصول زيادة)'
        elif balance < 0:
            context['balance_type'] = 'دائن (خسارة / التزامات زيادة)'
        else:
            context['balance_type'] = 'متوازن'

        return context

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'change_password.html'
    success_url = reverse_lazy('app:manager_dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'تم تغيير كلمة المرور بنجاح.')
        return super().form_valid(form)

from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy

class CustomPasswordChangeViewAcc(PasswordChangeView):
    template_name = 'change_passwordAcc.html'
    success_url = reverse_lazy('app:manager_dashboard')

    def form_valid(self, form):
        messages.success(self.request, 'تم تغيير كلمة المرور بنجاح.')
        return super().form_valid(form)