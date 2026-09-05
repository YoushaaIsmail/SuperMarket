from django.db import models
from decimal import Decimal
from django.contrib.auth.models import User,AbstractUser
from django.utils import timezone
import re
class User(AbstractUser):
    ROLE_CHOICES = (
        ('manager', 'مدير'),
        ('accountant', 'محاسب'),
     
   
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # يمكن إضافة حقول إضافية هنا إن لزم
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"

    class Meta:
        permissions = [
            ("can_manage_inventory", "Can manage inventory"),
            ("can_manage_sales", "Can manage sales"),
            ("can_view_financial_reports", "Can view financial reports"),
            ("can_manage_employes", "Can Manage Employes"),
        ]

class Category(models.Model):
    """فئة المنتج"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

class Unite(models.Model):
  
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Unites"

class Supplier(models.Model):
    """المورد"""
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    """العميل"""
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

from django.db.models import Q, Sum, F, Case, When, Value, IntegerField

class Product(models.Model):
    """المنتج"""
    image = models.ImageField(upload_to='Product/', null=True, blank=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    unite = models.ForeignKey(Unite, on_delete=models.SET_NULL, null=True, blank=True)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="سعر البيع بالدولار")
    sale_priceAmount = models.DecimalField(max_digits=10, decimal_places=2, help_text="سعر البيع بالدولار جملة")
    Pakage = models.PositiveIntegerField()
    Count_Alarm= models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    @property
    def total_quantity(self):
        """
        حساب الكمية المتاحة:
        مجموع المشتريات (غير المنتهية الصلاحية) مضروبة في Pakage إذا كانت Is_package=True
        مطروحاً منها مجموع المبيعات مضروبة في Pakage إذا كانت Is_package=True
        """
        # المشتريات (BatchProduct) غير المنتهية الصلاحية
        purchased = self.batches.filter(
            Q(expiration_date__isnull=True) | Q(expiration_date__gte=timezone.now().date())
        ).aggregate(
            total=Sum(
                Case(
                    When(Is_package=True, then=F('quantity') * F('product__Pakage')),
                    default=F('quantity'),
                    output_field=IntegerField()
                )
            )
        )['total'] or 0

        # المبيعات (SalesInvoiceDetail)
        sold = self.sale_details.aggregate(
            total=Sum(
                Case(
                    When(Is_package=True, then=F('quantity') * F('product__Pakage')),
                    default=F('quantity'),
                    output_field=IntegerField()
                )
            )
        )['total'] or 0

        return purchased - sold


    def __str__(self):
        return self.name


class ExchangeRate(models.Model):
    """سعر صرف الدولار مقابل الليرة السورية"""
    date = models.DateField(auto_now_add=True)
    rate = models.DecimalField(max_digits=12, decimal_places=2, help_text="سعر الدولار بالليرة السورية")

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"{self.date} - 1$ = {self.rate} SYP"


class PurchaseInvoice(models.Model):
    """فاتورة شراء"""
    invoice_number = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True,  # يسمح بتركه فارغاً عند الإضافة
        null=False,  # لكن في قاعدة البيانات لا يمكن أن يكون NULL
        help_text="يتم توليده تلقائياً إذا ترك فارغاً"
    )
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    exchange_rate = models.ForeignKey(ExchangeRate,models.CASCADE, null=True, blank=True,
                                      help_text="سعر الصرف المستخدم وقت الشراء")

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Purchase #{self.invoice_number} - {self.supplier.name}"
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_invoice_number():
        """توليد رقم فاتورة فريد بصيغة PO-YYYYMMDD-XXXX"""
        today = timezone.now().strftime('%Y%m%d')
        prefix = f"PO-{today}"
        # البحث عن آخر رقم تم استخدامه لهذا اليوم
        last_invoice = PurchaseInvoice.objects.filter(
            invoice_number__startswith=prefix
        ).order_by('-invoice_number').first()
        if last_invoice:
            # استخراج الرقم التسلسلي (XXXX) من آخر فاتورة
            match = re.search(r'(\d{4})$', last_invoice.invoice_number)
            if match:
                last_serial = int(match.group(1))
                new_serial = last_serial + 1
            else:
                new_serial = 1
        else:
            new_serial = 1
        return f"{prefix}-{new_serial:04d}"


class BatchProduct(models.Model):

    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='details')

    Is_package=models.BooleanField(default=False)
    """موديل دفعات الأدوية مع معلومات الصلاحية والكمية"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    quantity = models.PositiveIntegerField(default=0)
    expiration_date = models.DateField(null=True, blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # سعر الشراء
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['expiration_date']  # ترتيب حسب تاريخ الصلاحية
        verbose_name = 'Batch Product'
        verbose_name_plural = 'Batch Product'

    def __str__(self):
        return f"{self.product.name} - Qty: {self.quantity}"

    def is_available(self, needed=1):
        """Returns True if this batch has enough stock and not expired."""
        if self.expiration_date and self.expiration_date < timezone.now().date():
            return False
        return self.quantity >= needed

    @property
    def is_expired(self):
        """تحقق إذا انتهت صلاحية الدفعة"""
        if self.expiration_date:
            return self.expiration_date < timezone.now().date()
        return False

    @property
    def days_until_expiration(self):
        """عدد الأيام المتبقية حتى انتهاء الصلاحية"""
        if self.expiration_date:
            delta = self.expiration_date - timezone.now().date()
            return delta.days
        return None

class SalesInvoice(models.Model):
    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    exchange_rate = models.ForeignKey(ExchangeRate, on_delete=models.CASCADE, null=True, blank=True)
    Discount = models.DecimalField(max_digits=10, decimal_places=2, help_text="الخصم بالدولار")
    notes = models.TextField(blank=True, null=True)

class SalesInvoiceDetail(models.Model):
    """تفاصيل فاتورة البيع"""
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, related_name='details')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='sale_details')  # أضف related_name
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="سعر الوحدة بالدولار")
   
    Is_package=models.BooleanField(default=False)
    create_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='UserCreated')
   


class PaymentSales(models.Model):
 
    PAYMENT_METHODS = (
        ('cash', 'نقدي'),
        ('card', 'بطاقة'),
        ('transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
        ('other', 'أخرى'),
    )
    Customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='Payment_Customer',null=True,blank=True)  # يمكن استخدام GenericForeignKey لكن نبسطها
    amountDollar = models.DecimalField(max_digits=12, decimal_places=2, help_text="المبلغ بالدولار")
    amountSA = models.DecimalField(max_digits=12, decimal_places=2, help_text="المبلغ بالسوري")
    date = models.DateField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    exchange_rate_used = models.ForeignKey(ExchangeRate, on_delete=models.CASCADE, null=True, blank=True,
                                           help_text="سعر الصرف عند الدفع")
  
    notes = models.TextField(blank=True, null=True)
    create_by=models.ForeignKey(User, on_delete=models.CASCADE, related_name='UserCreatedPaymentSales')
    def __str__(self):
        return f"دفعة {self.get_invoice_type_display()} #{self.invoice_id} - {self.amount}$"



class PaymentPurchase(models.Model):
    """دفعة مرتبطة بفاتورة (شراء أو بيع)"""
    PAYMENT_METHODS = (
        ('cash', 'نقدي'),
        ('card', 'بطاقة'),
        ('transfer', 'تحويل بنكي'),
        ('check', 'شيك'),
        ('other', 'أخرى'),
    )
    Supplier_id = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name='Payment_Supplier')  # يمكن استخدام GenericForeignKey لكن نبسطها
    amountDollar = models.DecimalField(max_digits=12, decimal_places=2, help_text="المبلغ بالدولار")
    amountSA = models.DecimalField(max_digits=12, decimal_places=2, help_text="المبلغ بالسوري")
    date = models.DateField(auto_now_add=True)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    exchange_rate_used = models.ForeignKey(ExchangeRate, on_delete=models.CASCADE, null=True, blank=True,
                                           help_text="سعر الصرف عند الدفع")

    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"دفعة {self.get_invoice_type_display()} #{self.invoice_id} - {self.amount}$"




class Employee(models.Model):
    """موظفو الشركة (يمكن استخدامه أيضاً للعيادة)"""
    name = models.CharField(max_length=200, verbose_name="الاسم")
    position = models.CharField(max_length=100, verbose_name="الوظيفة")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='Employee',null=True,blank=True)

    # الراتب الأساسي الافتراضي (يمكن استخدامه كقاعدة)
    default_base_salary = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="الراتب الأساسي الافتراضي")
    hire_date = models.DateField(verbose_name="تاريخ التعيين")
    phone = models.CharField(max_length=20, verbose_name="رقم الهاتف")
    email = models.EmailField(blank=True, null=True, verbose_name="البريد الإلكتروني")
    bank_account = models.CharField(max_length=100, blank=True, null=True, verbose_name="رقم الحساب البنكي")
    is_active = models.BooleanField(default=True, verbose_name="نشط؟")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    
   



class ActionMoney_FullAll(models.Model):
    """علاوة مرتبطة بكشف راتب"""
    RELATIONSHIP_CHOICES = [
        ('Allowance', 'علاوة'),
        ('Penalty', 'عقوبة'),
     
  
    ]
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, verbose_name="العلاقة")
    Employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='allowances', verbose_name="كشف الراتب")
    description = models.CharField(max_length=200, verbose_name="الوصف")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    created_at = models.DateTimeField(auto_now_add=True)
  
    def __str__(self):
        return f"{self.description}: {self.amount}"
    



class SalaryPayment(models.Model):
    """سند صرف راتب (دفعة فعلية)"""
    Employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='payments', verbose_name="كشف الراتب")
    payment_date = models.DateField(auto_now_add=True, verbose_name="تاريخ الصرف")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ المدفوع")
    payment_method = models.CharField(max_length=50, verbose_name="طريقة الدفع")
    notes = models.TextField(blank=True, null=True, verbose_name="ملاحظات")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f" {self.amount} - {self.payment_date}"
    


class Action_Money_Month(models.Model):
    """علاوة مرتبطة بكشف راتب"""
    RELATIONSHIP_CHOICES = [
        ('Bonus', 'مكافأة'),
        ('advance', 'سلفة'),
   ('Deduction', 'خصم'),

  
    ]
    relationship = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES, verbose_name="العلاقة")
    Employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='Action_Money2SalaryPayment', verbose_name="كشف الراتب")
    description = models.CharField(max_length=200, verbose_name="الوصف")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.description}: {self.amount}"


class CostCategory(models.Model):
    """أنواع التكاليف"""
    name = models.CharField(max_length=100, unique=True, verbose_name="الفئة")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    
    def __str__(self):
        return self.name
    


class Cost(models.Model):
    """التكاليف التشغيلية"""
    category = models.ForeignKey(CostCategory, on_delete=models.CASCADE, related_name='costs', verbose_name="الفئة")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="المبلغ")
    date = models.DateField(verbose_name="التاريخ")
    description = models.TextField(blank=True, null=True, verbose_name="الوصف")
    
    def __str__(self):
        return f"{self.category.name} - {self.amount}"
    
 