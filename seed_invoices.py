from app.models import SalesInvoice, SalesInvoiceDetail, Customer, Product, ExchangeRate, User
from decimal import Decimal
from datetime import date
import random

print("🚀 بدء إنشاء فاتورة مبيعات جديدة...")

# 1. جلب أو إنشاء بيانات أساسية
customer = Customer.objects.first()
if not customer:
    print("⚠️ لا يوجد عملاء. سيتم إنشاء عميل تجريبي.")
    customer = Customer.objects.create(
        name="عميل تجريبي",
        phone="0912345678",
        email="test@example.com",
        address="دمشق - تجريبي"
    )

# 2. الحصول على مستخدم (منشئ الفاتورة)
user = User.objects.first()
if not user:
    print("⚠️ لا يوجد مستخدمين. سيتم إنشاء مستخدم تجريبي.")
    user = User.objects.create_user(
        username="test_user",
        password="password123",
        email="admin@example.com"
    )

# 3. الحصول على سعر الصرف
exchange_rate, created = ExchangeRate.objects.get_or_create(
    rate=Decimal('15000.00'),
    defaults={'date': date.today()}
)
print(f"✅ سعر الصرف: 1$ = {exchange_rate.rate} ل.س")

# 4. اختيار 3 منتجات عشوائية (أو أول 3 منتجات إذا لم يكن هناك تنوع)
products = list(Product.objects.all())
if len(products) < 3:
    print("⚠️ عدد المنتجات أقل من 3. سيتم استخدام ما هو متاح.")
    selected_products = products
else:
    selected_products = random.sample(products, 3)

if not selected_products:
    print("❌ لا توجد منتجات. أضف منتجات أولاً.")
    exit()

# 5. إنشاء الفاتورة
invoice = SalesInvoice.objects.create(
    customer=customer,
    exchange_rate=exchange_rate,
    Discount=Decimal('5.00'),  # خصم 5 دولار
    notes="فاتورة مبيعات تجريبية #1",
    date=date.today()
)
print(f"📄 تم إنشاء الفاتورة: {invoice.invoice_number}")

# 6. إضافة تفاصيل الفاتورة (المنتجات)
total_before_discount = Decimal('0.00')
for product in selected_products:
    # نختار سعر البيع (قطاعي أو جملة) بشكل عشوائي
    is_package = random.choice([True, False])
    price = product.sale_priceAmount if is_package else product.sale_price
    quantity = random.randint(1, 5)

    detail = SalesInvoiceDetail.objects.create(
        invoice=invoice,
        product=product,
        quantity=quantity,
        price=price,
        Is_package=is_package,
        create_by=user
    )
    subtotal = quantity * price
    total_before_discount += subtotal
    print(f"   ✅ {product.name} x {quantity} = ${subtotal:.2f} ({'جملة' if is_package else 'قطاعي'})")

# 7. حساب الإجماليات
net_total = total_before_discount - invoice.Discount
print("\n" + "="*50)
print(f"💰 إجمالي الفاتورة (قبل الخصم): ${total_before_discount:.2f}")
print(f"💰 الخصم: ${invoice.Discount:.2f}")
print(f"💰 صافي الفاتورة: ${net_total:.2f}")
print(f"💰 صافي الفاتورة بالليرة السورية: {net_total * exchange_rate.rate:.2f} ل.س")
print("="*50)