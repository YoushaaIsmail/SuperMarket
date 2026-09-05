from django.urls import path
from . import views

urlpatterns = [
    path('', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('manager-dashboard/', views.manager_dashboard, name='manager_dashboard'),
    path('accountant-dashboard/', views.accountant_dashboard, name='accountant_dashboard'),

        path('inventory/', views.InventoryDashboardView.as_view(), name='inventory_dashboard'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),

        path('unites/', views.UniteListView.as_view(), name='unite_list'),
    path('unites/add/', views.UniteCreateView.as_view(), name='unite_add'),
    path('unites/<int:pk>/edit/', views.UniteUpdateView.as_view(), name='unite_edit'),
    path('unites/<int:pk>/delete/', views.UniteDeleteView.as_view(), name='unite_delete'),

path('exchange-rates/', views.ExchangeRateListView.as_view(), name='exchange_rate_list'),
path('exchange-rates/add/', views.ExchangeRateCreateView.as_view(), name='exchange_rate_add'),
path('exchange-rates/<int:pk>/edit/', views.ExchangeRateUpdateView.as_view(), name='exchange_rate_edit'),
path('exchange-rates/<int:pk>/delete/', views.ExchangeRateDeleteView.as_view(), name='exchange_rate_delete'),

# Customer Management
path('customers/', views.CustomerListView.as_view(), name='customer_list'),
path('customers/add/', views.CustomerCreateView.as_view(), name='customer_add'),
path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_edit'),
path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),

path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
path('suppliers/add/', views.SupplierCreateView.as_view(), name='supplier_add'),
path('suppliers/<int:pk>/edit/', views.SupplierUpdateView.as_view(), name='supplier_edit'),
path('suppliers/<int:pk>/delete/', views.SupplierDeleteView.as_view(), name='supplier_delete'),

path('purchase-invoices/', views.PurchaseInvoiceListView.as_view(), name='purchase_invoice_list'),
path('purchase-invoices/add/', views.PurchaseInvoiceCreateView.as_view(), name='purchase_invoice_add'),
path('purchase-invoices/<int:pk>/edit/', views.PurchaseInvoiceUpdateView.as_view(), name='purchase_invoice_edit'),
path('purchase-invoices/<int:pk>/delete/', views.PurchaseInvoiceDeleteView.as_view(), name='purchase_invoice_delete'),

        path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
        path('products/barcode/<str:barcode>/', views.ProductDetailByBarcodeView.as_view(), name='product_by_barcode'),
        path('check-barcode/', views.check_barcode, name='check_barcode'),
        path('products/by-barcode/', views.ProductByBarcodeView.as_view(), name='product_by_barcode_ajax'),
        path('generate-invoice-number/', views.GenerateInvoiceNumberView.as_view(), name='generate_invoice_number'),
 path('password-reset/', views.password_reset_request, name='password_reset_request'),
        path('payment-purchases/', views.PaymentPurchaseListView.as_view(), name='payment_purchase_list'),
path('payment-purchases/add/', views.PaymentPurchaseCreateView.as_view(), name='payment_purchase_add'),
path('payment-purchases/<int:pk>/edit/', views.PaymentPurchaseUpdateView.as_view(), name='payment_purchase_edit'),
path('payment-purchases/<int:pk>/delete/', views.PaymentPurchaseDeleteView.as_view(), name='payment_purchase_delete'),
path('financial-statistics/', views.FinancialReportView.as_view(), name='financial_statistics'),

    path('sales-invoices/', views.SalesInvoiceListView.as_view(), name='sales_invoice_list'),
    # عرض فاتورة
    path('sales-invoices/<int:pk>/', views.SalesInvoiceDetailView.as_view(), name='invoice_detail'),
    # إضافة فاتورة
    path('sales-invoices/add/', views.sales_invoice_create, name='sales_invoice_add'),
    # تعديل فاتورة
    path('sales-invoices/<int:pk>/edit/', views.SalesInvoiceUpdateView.as_view(), name='invoice_edit'),
    # حذف فاتورة
    path('sales-invoices/<int:pk>/delete/', views.SalesInvoiceDeleteView.as_view(), name='invoice_delete'),
    path('get-product-price/', views.get_product_price, name='get_product_price'), 
path('change-password/', views.CustomPasswordChangeView.as_view(), name='change_password'),
path('change-passwordAcc/', views.CustomPasswordChangeViewAcc.as_view(), name='CustomPasswordChangeViewAcc'),
path('payments-sales/', views.PaymentSalesListView.as_view(), name='payment_sales_list'),
path('payments-sales/add/', views.PaymentSalesCreateView.as_view(), name='payment_sales_add'),
path('payments-sales/<int:pk>/edit/', views.PaymentSalesUpdateView.as_view(), name='payment_sales_edit'),
path('payments-sales/<int:pk>/delete/', views.PaymentSalesDeleteView.as_view(), name='payment_sales_delete'),
# HR Management
path('hr/dashboard/', views.HRDashboardView.as_view(), name='hr_dashboard'),
path('employees/', views.EmployeeListView.as_view(), name='employee_list'),
path('employees/add/', views.EmployeeCreateView.as_view(), name='employee_add'),
    path('employees/<int:pk>/edit/', views.EmployeeUpdateView.as_view(), name='employee_edit'),
    path('employees/<int:pk>/delete/', views.EmployeeDeleteView.as_view(), name='employee_delete'),

path('users/', views.UserListView.as_view(), name='user_list'),
path('users/add/', views.UserCreateView.as_view(), name='user_add'),
path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
path('users/<int:pk>/change-password/', views.UserChangePasswordView.as_view(), name='user_change_password'),
# Supplier Account
path('suppliers/<int:pk>/account/', views.SupplierAccountView.as_view(), name='supplier_account'),
# Action Money (Allowances & Penalties)
path('employees/<int:employee_id>/allowances/', views.ActionMoneyFullAllListView.as_view(), name='allowance_list'),
path('employees/<int:employee_id>/allowances/add/', views.ActionMoneyFullAllCreateView.as_view(), name='allowance_add'),
path('allowances/<int:pk>/edit/', views.ActionMoneyFullAllUpdateView.as_view(), name='allowance_edit'),
path('allowances/<int:pk>/delete/', views.ActionMoneyFullAllDeleteView.as_view(), name='allowance_delete'),

path('employees/<int:employee_id>/payments/', views.SalaryPaymentListView.as_view(), name='salary_payment_list'),
path('employees/<int:employee_id>/payments/add/', views.SalaryPaymentCreateView.as_view(), name='salary_payment_add'),
path('salary-payments/<int:pk>/edit/', views.SalaryPaymentUpdateView.as_view(), name='salary_payment_edit'),
path('salary-payments/<int:pk>/delete/', views.SalaryPaymentDeleteView.as_view(), name='salary_payment_delete'),

# Action Money Month (Bonus, Advance, Deduction) - المكافآت، السلف، الخصومات الشهرية
path('employees/<int:employee_id>/monthly-actions/', views.ActionMoneyMonthListView.as_view(), name='monthly_action_list'),
path('employees/<int:employee_id>/monthly-actions/add/', views.ActionMoneyMonthCreateView.as_view(), name='monthly_action_add'),
path('monthly-actions/<int:pk>/edit/', views.ActionMoneyMonthUpdateView.as_view(), name='monthly_action_edit'),
path('monthly-actions/<int:pk>/delete/', views.ActionMoneyMonthDeleteView.as_view(), name='monthly_action_delete'),
path('employees/<int:employee_id>/salary-report/', views.EmployeeSalaryReportView.as_view(), name='employee_salary_report'),

path('cost-categories/', views.CostCategoryListView.as_view(), name='cost_category_list'),
path('cost-categories/add/', views.CostCategoryCreateView.as_view(), name='cost_category_add'),
path('cost-categories/<int:pk>/edit/', views.CostCategoryUpdateView.as_view(), name='cost_category_edit'),
path('cost-categories/<int:pk>/delete/', views.CostCategoryDeleteView.as_view(), name='cost_category_delete'),

path('cost-categories/<int:category_id>/costs/', views.CostListView.as_view(), name='cost_list'),
path('cost-categories/<int:category_id>/costs/add/', views.CostCreateView.as_view(), name='cost_add'),
path('costs/<int:pk>/edit/', views.CostUpdateView.as_view(), name='cost_edit'),
path('costs/<int:pk>/delete/', views.CostDeleteView.as_view(), name='cost_delete'),
# ]
]