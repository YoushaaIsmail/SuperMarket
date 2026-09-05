from django import forms
from django.forms import inlineformset_factory
from .models import *

class PurchaseInvoiceForm(forms.ModelForm):
    class Meta:
        model = PurchaseInvoice
        fields = ['invoice_number', 'supplier', 'exchange_rate', 'notes']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-control'}),
            'exchange_rate': forms.Select(attrs={'class': 'form-control'}),
            
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class BatchProductForm(forms.ModelForm):
    class Meta:
        model = BatchProduct
        fields = ['product', 'quantity', 'expiration_date', 'purchase_price', 'Is_package']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'purchase_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'Is_package': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# إنشاء Formset للدفعات
BatchProductFormSet = inlineformset_factory(
    PurchaseInvoice, 
    BatchProduct, 
    form=BatchProductForm,
    extra=1,  # عدد الدفعات الفارغة المعروضة
    can_delete=True
)
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'phone', 'address', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CustomUserChangeForm(UserChangeForm):
    password = None  # لإخفاء حقل كلمة المرور من نموذج التعديل

    class Meta:
        model = User
        fields = ('username', 'email', 'role', 'phone', 'address')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class SalesInvoiceForm(forms.ModelForm):
    class Meta:
        model = SalesInvoice
        fields = ['invoice_number', 'customer', 'exchange_rate', 'Discount', 'notes']
        widgets = {
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control form-control-modern',
                'readonly': False,  # يسمح بالتعديل ولكن يمكن تعبئته تلقائياً
                'placeholder': 'سيتم إنشاؤه تلقائياً'
            }),
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'exchange_rate': forms.Select(attrs={'class': 'form-control'}),
            'Discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # جعل رقم الفاتورة غير مطلوب (لأننا سنولده تلقائياً)
        self.fields['invoice_number'].required = False
# formset للتفاصيل (سنستخدمه لكننا سنضيف الصفوف يدوياً في القالب)
SalesInvoiceDetailFormSet = forms.inlineformset_factory(
    SalesInvoice,
    SalesInvoiceDetail,
    fields=['product', 'quantity', 'price', 'Is_package'],
    extra=0,  # لا نريد صفوفاً فارغة، سنضيفها يدوياً
    can_delete=True,
)

class SalesInvoiceDetailForm(forms.ModelForm):
    class Meta:
        model = SalesInvoiceDetail
        fields = ['product', 'quantity', 'price', 'Is_package']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control quantity-input', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control price-input', 'step': '0.01'}),
            'Is_package': forms.CheckboxInput(attrs={'class': 'form-check-input package-checkbox'}),
        }

class SalesInvoiceDetailForm(forms.ModelForm):
    class Meta:
        model = SalesInvoiceDetail
        fields = ['product', 'quantity', 'price', 'Is_package']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control product-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'Is_package': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

from django import forms
from .models import PaymentSales, SalesInvoice

class PaymentSalesForm(forms.ModelForm):
    class Meta:
        model = PaymentSales
        fields = ['Customer_id', 'amountSA','amountDollar', 'method', 'exchange_rate_used', 'notes']
        widgets = {
            'Customer_id': forms.Select(attrs={'class': 'form-control'}),
            'amountSA': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
             'amountDollar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'method': forms.Select(attrs={'class': 'form-control'}),
            'exchange_rate_used': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تخصيص عرض الفواتير في القائمة المنسدلة

class ActionMoneyFullAllForm(forms.ModelForm):
    class Meta:
        model = ActionMoney_FullAll
        fields = ['relationship', 'description', 'amount']
        widgets = {
            'relationship': forms.Select(attrs={
                'class': 'form-control form-control-modern',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control form-control-modern',
                'rows': 3,
                'placeholder': 'أدخل وصفاً توضيحياً (اختياري)',
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-modern',
                'step': '0.01',
                'placeholder': '0.00',
            }),
        }
        labels = {
            'relationship': 'النوع',
            'description': 'الوصف',
            'amount': 'المبلغ ($)',
        }
        error_messages = {
            'relationship': {
                'required': 'يرجى اختيار نوع العلاوة/العقوبة.',
            },
            'amount': {
                'required': 'المبلغ مطلوب.',
                'invalid': 'يرجى إدخال رقم صحيح.',
            },
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount < 0:
            raise forms.ValidationError('المبلغ لا يمكن أن يكون سالباً.')
        return amount


class SalaryPaymentForm(forms.ModelForm):
    class Meta:
        model = SalaryPayment
        fields = ['amount', 'payment_method', 'notes']
        widgets = {
            'amount': forms.NumberInput(attrs={
                'class': 'form-control form-control-modern',
                'step': '0.01',
                'placeholder': '0.00',
            }),
            'payment_method': forms.TextInput(attrs={'class': 'form-control form-control-modern',
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-modern',
                'rows': 3,
                'placeholder': 'ملاحظات إضافية (اختياري)',
            }),
        }
        labels = {
            'amount': 'المبلغ ($)',
            'payment_method': 'طريقة الدفع',
            'notes': 'ملاحظات',
        }
        error_messages = {
            'amount': {
                'required': 'المبلغ مطلوب.',
                'invalid': 'يرجى إدخال رقم صحيح.',
            },
            'payment_method': {
                'required': 'يرجى اختيار طريقة الدفع.',
            },
        }

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise forms.ValidationError('المبلغ يجب أن يكون أكبر من صفر.')
        return amount

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = [
            'name', 'position', 'user', 'default_base_salary',
            'hire_date', 'phone', 'email', 'bank_account', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control form-control-modern', 'placeholder': 'أدخل اسم الموظف'}),
            'position': forms.TextInput(attrs={'class': 'form-control form-control-modern', 'placeholder': 'مثال: مدير مبيعات'}),
            'user': forms.Select(attrs={'class': 'form-control form-control-modern'}),
            'default_base_salary': forms.NumberInput(attrs={'class': 'form-control form-control-modern', 'step': '0.01', 'placeholder': '0.00'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control form-control-modern', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'form-control form-control-modern', 'placeholder': '09xxxxxxxx'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-modern', 'placeholder': 'example@domain.com'}),
            'bank_account': forms.TextInput(attrs={'class': 'form-control form-control-modern', 'placeholder': 'رقم الحساب البنكي'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': 'الاسم',
            'position': 'الوظيفة',
            'user': 'حساب المستخدم',
            'default_base_salary': 'الراتب الأساسي ($)',
            'hire_date': 'تاريخ التعيين',
            'phone': 'رقم الهاتف',
            'email': 'البريد الإلكتروني',
            'bank_account': 'رقم الحساب البنكي',
            'is_active': 'نشط',
        }
        help_texts = {
            'user': 'اختر حساب مستخدم مرتبط بالموظف (اختياري)',
            'default_base_salary': 'الراتب الأساسي الشهري بالدولار',
            'bank_account': 'رقم الحساب البنكي لتحويل الراتب',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # تعيين تاريخ اليوم كقيمة افتراضية لحقل تاريخ التعيين
        if not self.instance.pk and not self.data.get('hire_date'):
            self.initial['hire_date'] = timezone.now().date().isoformat()

        # إضافة كلاسات إضافية لبعض الحقول
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['user'].empty_label = '-- اختر حساب مستخدم --'

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise forms.ValidationError('رقم الهاتف يجب أن يحتوي على أرقام فقط.')
        return phone

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # يمكن إضافة تحقق إضافي هنا
            pass
        return email