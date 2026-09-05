# salary_utils.py
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db.models import Sum
from .models import Employee, ActionMoney_FullAll, Action_Money_Month, SalaryPayment


def calculate_monthly_salary(employee, up_to_date=None, advance_installments=1):
    """
    حساب الراتب الشهري للموظف اعتباراً من تاريخ التعيين
    
    المعاملات:
    - employee: الموظف
    - up_to_date: تاريخ الانتهاء (اختياري)
    - advance_installments: عدد الأشهر لتقسيم السلفة (افتراضي 1 يعني خصم كامل السلفة في شهر واحد)
    
    المنطق:
    1. العلاوات والعقوبات من ActionMoney_FullAll: تطبق من تاريخ created_at وتستمر للأبد
    2. المكافآت والخصومات من Action_Money_Month: فقط في شهر تسجيلها (لمرة واحدة)
    3. السلف من Action_Money_Month: تقسط على عدد الأشهر المحدد
    """
    print(f"\n{'='*60}")
    print(f"حساب الراتب للموظف: {employee.name} (ID: {employee.id})")
    print(f"تاريخ التعيين: {employee.hire_date}")
    print(f"تاريخ الانتهاء: {up_to_date if up_to_date else 'اليوم'}")
    print(f"تقسيم السلفة على: {advance_installments} شهر(أشهر)")
    print(f"{'='*60}")
    
    if up_to_date is None:
        up_to_date = datetime.today().date()

    hire_date = employee.hire_date
    if hire_date > up_to_date:
        print("⚠️ تاريخ التعيين بعد تاريخ الانتهاء - لا توجد دورات")
        return []

    results = []
    
    # ============ جمع بيانات السلف (لتقسيمها) ============
    total_advances = Action_Money_Month.objects.filter(
        Employee=employee,
        relationship='advance'
    ).aggregate(total=Sum('amount'))['total'] or 0
    total_advances = float(total_advances)
    
    monthly_advance_installment = total_advances / advance_installments if advance_installments > 0 else total_advances
    remaining_advance_balance = total_advances
    
    print(f"📌 إجمالي السلف: {total_advances} (سيتم خصم {monthly_advance_installment} شهرياً)")
    print(f"📌 عدد أقساط السلفة: {advance_installments}")
    print(f"{'='*60}\n")
    
    # متغيرات التتبع
    total_paid_until_previous = 0
    
    period_start = hire_date
    cycle_count = 0

    while period_start <= up_to_date:
        cycle_count += 1
        period_end = period_start + relativedelta(months=1) - timedelta(days=1)

        if period_end > up_to_date:
            period_end = up_to_date

        print(f"\n--- الدورة {cycle_count}: {period_start} → {period_end} ---")
        
        # الراتب الأساسي
        base = float(employee.default_base_salary)
        print(f"  الراتب الأساسي: {base}")

        # ============ العلاوات والعقوبات السارية في هذه الدورة ============
        # تجمع كل العلاوات التي created_at <= نهاية الدورة (أي صدرت قبل أو خلال هذه الدورة)
        allowances_up_to_now = ActionMoney_FullAll.objects.filter(
            Employee=employee,
            relationship='Allowance',
            created_at__date__lte=period_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        penalties_up_to_now = ActionMoney_FullAll.objects.filter(
            Employee=employee,
            relationship='Penalty',
            created_at__date__lte=period_end
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        allowance_this_month = float(allowances_up_to_now)
        penalty_this_month = float(penalties_up_to_now)
        
        print(f"  العلاوات السارية حتى هذا الشهر: {allowance_this_month}")
        print(f"  العقوبات السارية حتى هذا الشهر: {penalty_this_month}")

        # ============ Action_Money_Month (عناصر لمرة واحدة في هذا الشهر) ============
        month_actions2 = Action_Money_Month.objects.filter(
            Employee=employee,
            created_at__date__gte=period_start,
            created_at__date__lte=period_end
        )
        month_bonus = float(month_actions2.filter(relationship='Bonus').aggregate(s=Sum('amount'))['s'] or 0)
        month_deduction = float(month_actions2.filter(relationship='Deduction').aggregate(s=Sum('amount'))['s'] or 0)
        
        print(f"  المكافآت (هذا الشهر فقط): {month_bonus}")
        print(f"  الخصومات (هذا الشهر فقط): {month_deduction}")
            
        # ============ حساب إجمالي الراتب قبل السلفة ============
        total_before_advance = base + allowance_this_month - penalty_this_month + month_bonus - month_deduction
        print(f"  إجمالي الراتب قبل خصم السلفة: {total_before_advance}")

        # ============ خصم قسط السلفة الشهري ============
        if remaining_advance_balance > 0:
            advance_deduction = min(monthly_advance_installment, remaining_advance_balance)
            advance_deduction = min(advance_deduction, max(total_before_advance, 0))
            remaining_advance_balance -= advance_deduction
        else:
            advance_deduction = 0
            
        print(f"  رصيد السلفة المتبقي قبل الخصم: {remaining_advance_balance + advance_deduction}")
        print(f"  خصم السلفة هذا الشهر: {advance_deduction}")
        print(f"  رصيد السلفة المتبقي بعد الخصم: {remaining_advance_balance}")

        # ============ صافي الراتب قبل الدفعات ============
        net_before_payments = total_before_advance - advance_deduction
        net_before_payments = max(net_before_payments, 0)
        print(f"  صافي الراتب (قبل الدفعات): {net_before_payments}")

        # ============ الدفعات المدفوعة (SalaryPayment) ============
        period_payments = SalaryPayment.objects.filter(
            Employee=employee,
            payment_date__gte=period_start,
            payment_date__lte=period_end
        )
        total_paid_this_period = float(period_payments.aggregate(s=Sum('amount'))['s'] or 0)
        print(f"  الدفعات المدفوعة هذا الشهر: {total_paid_this_period}")

        # ============ حساب الراتب النهائي بعد الدفعات ============
        total_earned = net_before_payments + total_paid_until_previous
        total_paid_until_current = total_paid_until_previous + total_paid_this_period
        
        remaining_salary = total_earned - total_paid_until_current
        current_net = remaining_salary if remaining_salary > 0 else 0
        advance_payment_balance = abs(remaining_salary) if remaining_salary < 0 else 0
        
        total_paid_until_previous = total_paid_until_current
        
        print(f"  إجمالي المستحق (تراكمي): {total_earned}")
        print(f"  إجمالي المدفوع (تراكمي): {total_paid_until_current}")
        print(f"  صافي الراتب لهذا الشهر: {current_net}")
        print(f"  الراتب المتبقي (تراكمي): {remaining_salary}")

        results.append({
            'period_label': f"{period_start.strftime('%Y-%m-%d')} → {period_end.strftime('%Y-%m-%d')}",
            'period_start': period_start.strftime('%Y-%m-%d'),
            'period_end': period_end.strftime('%Y-%m-%d'),
            'base_salary': base,
            'allowance_this_month': allowance_this_month,
            'penalty_this_month': penalty_this_month,
            'month_bonus': month_bonus,
            'month_deduction': month_deduction,
            'advance_deducted_this_month': advance_deduction,
            'remaining_advance_balance': remaining_advance_balance,
            'net_before_payments': net_before_payments,
            'payments_this_period': total_paid_this_period,
            'total_paid_to_date': total_paid_until_current,
            'net_salary': current_net,
            'remaining_debt': advance_payment_balance,
            'total_earned_accumulated': total_earned,
        })

        period_start = period_end + timedelta(days=1)

    print(f"\n{'='*60}")
    print(f"✅ اكتمل الحساب - إجمالي {cycle_count} دورة")
    print(f"{'='*60}\n")
    
    return results


def summarize_monthly_salary(employee, up_to_date=None, advance_installments=1):
    """
    تلخيص الراتب الشهري للموظف
    
    المعاملات:
    - advance_installments: عدد الأشهر لتقسيم السلفة
    """
    print(f"\n📊 تلخيص الراتب للموظف: {employee.name}")
    
    monthly_data = calculate_monthly_salary(employee, up_to_date, advance_installments)
    if not monthly_data:
        print("⚠️ لا توجد بيانات للتلخيص")
        return None
    
    total_net_before_payments = sum(d['net_before_payments'] for d in monthly_data)
    total_payments = sum(d['payments_this_period'] for d in monthly_data)
    total_net_after_payments = sum(d['net_salary'] for d in monthly_data)
    total_remaining_debt = sum(d['remaining_debt'] for d in monthly_data)
    
    # حساب إجمالي العلاوات والعقوبات (مرة واحدة فقط)
    total_allowances = ActionMoney_FullAll.objects.filter(
        Employee=employee, relationship='Allowance'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_penalties = ActionMoney_FullAll.objects.filter(
        Employee=employee, relationship='Penalty'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_bonus = Action_Money_Month.objects.filter(
        Employee=employee, relationship='Bonus'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_advances = Action_Money_Month.objects.filter(
        Employee=employee, relationship='advance'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_deductions = Action_Money_Month.objects.filter(
        Employee=employee, relationship='Deduction'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    summary = {
        'employee_name': employee.name,
        'employee_id': employee.id,
        'position': employee.position,
        'hire_date': employee.hire_date.strftime('%Y-%m-%d'),
        'base_salary': float(employee.default_base_salary),
        'period_from': monthly_data[0]['period_start'],
        'period_to': monthly_data[-1]['period_end'],
        'cycles_count': len(monthly_data),
        'total_net_before_payments': total_net_before_payments,
        'total_payments_made': total_payments,
        'total_net_after_payments': total_net_after_payments,
        'total_remaining_debt': total_remaining_debt,
        'total_allowances': float(total_allowances),
        'total_penalties': float(total_penalties),
        'total_bonus': float(total_bonus),
        'total_advances': float(total_advances),
        'total_deductions': float(total_deductions),
        'remaining_advance_balance': monthly_data[-1]['remaining_advance_balance'],
        'advance_installments': advance_installments,
        'total_earned_accumulated': monthly_data[-1]['total_earned_accumulated'],
    }
    
    print(f"\n📋 ملخص التقرير:")
    print(f"  اسم الموظف: {summary['employee_name']}")
    print(f"  الراتب الأساسي: {summary['base_salary']}")
    print(f"  عدد الدورات: {summary['cycles_count']}")
    print(f"  إجمالي العلاوات (تراكمي): {summary['total_allowances']}")
    print(f"  إجمالي العقوبات (تراكمي): {summary['total_penalties']}")
    print(f"  إجمالي المكافآت (لمرة واحدة): {summary['total_bonus']}")
    print(f"  إجمالي السلف: {summary['total_advances']}")
    print(f"  إجمالي الخصومات (لمرة واحدة): {summary['total_deductions']}")
    print(f"  ---")
    print(f"  الراتب المستحق (قبل الدفعات): {summary['total_net_before_payments']}")
    print(f"  إجمالي الدفعات المدفوعة: {summary['total_payments_made']}")
    print(f"  صافي الراتب المستحق: {summary['total_net_after_payments']}")
    print(f"  المتبقي من السلف: {summary['remaining_advance_balance']}")
    print(f"  إجمالي ما استحقه الموظف: {summary['total_earned_accumulated']}")
    
    return summary


# ============ واجهة سهلة للاستخدام ============
def get_employee_salary_report(employee_id, up_to_date=None, advance_installments=3):
    """
    واجهة سهلة للحصول على تقرير راتب الموظف
    
    المعاملات:
    - employee_id: معرف الموظف
    - up_to_date: تاريخ الانتهاء (اختياري)
    - advance_installments: عدد أشهر تقسيط السلفة (افتراضي 3 أشهر)
    """
    try:
        employee = Employee.objects.get(id=employee_id)
        
        # حساب الراتب الشهري
        monthly_breakdown = calculate_monthly_salary(employee, up_to_date, advance_installments)
        
        # تلخيص الراتب
        summary = summarize_monthly_salary(employee, up_to_date, advance_installments)
        
        return {
            'success': True,
            'monthly_breakdown': monthly_breakdown,
            'summary': summary
        }
    except Employee.DoesNotExist:
        return {
            'success': False,
            'error': f'الموظف بالرقم {employee_id} غير موجود'
        }