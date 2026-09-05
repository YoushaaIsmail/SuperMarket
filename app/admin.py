from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password
from django.apps import apps
from .models import *

# ---------- Register all other models automatically ----------
app_models = apps.get_app_config('app').get_models()  # replace with your app name
# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
User = get_user_model()

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # حقول الإضافة (كما لديك)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'address', 'phone', 'role','first_name','last_name','email'),
        }),
    )

    # حقول التعديل (أضف هذا)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('معلومات شخصية', {'fields': ('address', 'phone', 'role','first_name','last_name','email')}),
        ('الصلاحيات', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('تواريخ مهمة', {'fields': ('last_login', 'date_joined')}),
    )
    # ملاحظة: password في fieldsets سيظهر كحقل غير قابل للتعديل (يظهر فقط رابط لتغيير كلمة المرور).
for model in app_models:
    if  model :   # skip Shop
        try:
            admin.site.register(model)
        except admin.sites.AlreadyRegistered:
            pass
