"""
View to add demo data via web URL (for production testing without shell access)
Only accessible to superusers
"""
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from .models import Expense, Category, MonthlyBudget, CategoryBudget


@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_demo_data(request):
    """
    Web endpoint to add demo data
    Only accessible to superusers
    URL: /demo-data/add/
    """
    user = request.user
    
    # Create categories
    categories_data = [
        ('Food & Dining', ['Breakfast', 'Lunch', 'Dinner', 'Groceries', 'Snacks']),
        ('Transport', ['Gas', 'Metro', 'Uber', 'Parking', 'Auto']),
        ('Entertainment', ['Movies', 'Gaming', 'Streaming', 'Concert', 'Sports']),
        ('Shopping', ['Clothes', 'Electronics', 'Books', 'Gadgets', 'Shoes']),
        ('Bills & Utilities', ['Internet', 'Electricity', 'Water', 'Phone', 'Gas Bill']),
    ]
    
    created_categories = {}
    categories_created = 0
    
    for cat_name, _ in categories_data:
        category, created = Category.objects.get_or_create(
            user=user,
            name=cat_name
        )
        created_categories[cat_name] = category
        if created:
            categories_created += 1
    
    # Create monthly budget
    now = timezone.now()
    budget, budget_created = MonthlyBudget.objects.get_or_create(
        user=user,
        year=now.year,
        month=now.month,
        defaults={'amount': Decimal('50000.00')}
    )
    
    # Create category budgets
    category_budgets_data = {
        'Food & Dining': Decimal('15000.00'),
        'Transport': Decimal('8000.00'),
        'Entertainment': Decimal('5000.00'),
        'Shopping': Decimal('10000.00'),
        'Bills & Utilities': Decimal('7000.00'),
    }
    
    cat_budgets_created = 0
    for cat_name, amount in category_budgets_data.items():
        if cat_name in created_categories:
            _, created = CategoryBudget.objects.get_or_create(
                user=user,
                category=created_categories[cat_name],
                year=now.year,
                month=now.month,
                defaults={'amount': amount}
            )
            if created:
                cat_budgets_created += 1
    
    # Add expenses for last 3 months
    expenses_added = 0
    
    for month_offset in range(3):
        month_date = now - timedelta(days=30 * month_offset)
        
        for cat_name, expense_types in categories_data:
            category = created_categories[cat_name]
            num_expenses = random.randint(5, 15)
            
            for _ in range(num_expenses):
                expense_type = random.choice(expense_types)
                
                # Random amount by category
                if cat_name == 'Food & Dining':
                    amount = Decimal(str(random.randint(50, 800)))
                elif cat_name == 'Transport':
                    amount = Decimal(str(random.randint(30, 500)))
                elif cat_name == 'Entertainment':
                    amount = Decimal(str(random.randint(100, 1500)))
                elif cat_name == 'Shopping':
                    amount = Decimal(str(random.randint(200, 5000)))
                else:
                    amount = Decimal(str(random.randint(500, 2500)))
                
                day = random.randint(1, 28)
                expense_date = datetime(month_date.year, month_date.month, day).date()
                
                Expense.objects.create(
                    user=user,
                    category=category,
                    title=expense_type,
                    amount=amount,
                    expense_date=expense_date,
                    notes=f'Demo {expense_type.lower()}',
                    is_deleted=False
                )
                expenses_added += 1
    
    # Add anomaly
    Expense.objects.create(
        user=user,
        category=created_categories['Shopping'],
        title='Laptop Purchase',
        amount=Decimal('85000.00'),
        expense_date=now.date(),
        notes='High-value purchase for anomaly testing',
        is_deleted=False
    )
    expenses_added += 1
    
    # Generate response
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demo Data Added</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f9fafb;
            }}
            .success {{
                background: #10b981;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .stats {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            .stat-item {{
                padding: 10px 0;
                border-bottom: 1px solid #e5e7eb;
            }}
            .stat-item:last-child {{
                border-bottom: none;
            }}
            .btn {{
                display: inline-block;
                background: #6366f1;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                margin-top: 20px;
            }}
            .btn:hover {{
                background: #4f46e5;
            }}
        </style>
    </head>
    <body>
        <div class="success">
            <h1>✅ Demo Data Added Successfully!</h1>
            <p>AI insights data has been generated for user: <strong>{user.email}</strong></p>
        </div>
        
        <div class="stats">
            <h2>📊 Summary</h2>
            <div class="stat-item">
                <strong>Categories:</strong> {len(created_categories)} ({categories_created} new)
            </div>
            <div class="stat-item">
                <strong>Expenses:</strong> {expenses_added} (across 3 months)
            </div>
            <div class="stat-item">
                <strong>Monthly Budget:</strong> ₹50,000
            </div>
            <div class="stat-item">
                <strong>Category Budgets:</strong> {len(category_budgets_data)} ({cat_budgets_created} new)
            </div>
            <div class="stat-item">
                <strong>Anomaly:</strong> Laptop Purchase (₹85,000)
            </div>
        </div>
        
        <a href="/dashboard/" class="btn">🚀 View Dashboard & AI Insights</a>
    </body>
    </html>
    """
    
    return HttpResponse(html)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def clear_demo_data(request):
    """
    Web endpoint to clear demo data
    Only accessible to superusers
    URL: /demo-data/clear/
    """
    user = request.user
    
    # Clear data
    expenses_deleted = Expense.objects.filter(user=user).count()
    Expense.objects.filter(user=user).delete()
    CategoryBudget.objects.filter(user=user).delete()
    MonthlyBudget.objects.filter(user=user).delete()
    categories_deleted = Category.objects.filter(user=user).count()
    Category.objects.filter(user=user).delete()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demo Data Cleared</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
                background: #f9fafb;
            }}
            .warning {{
                background: #ef4444;
                color: white;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            .btn {{
                display: inline-block;
                background: #6366f1;
                color: white;
                padding: 12px 24px;
                text-decoration: none;
                border-radius: 6px;
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="warning">
            <h1>🗑️ Demo Data Cleared</h1>
            <p>All data for user <strong>{user.email}</strong> has been deleted</p>
            <p>Deleted: {expenses_deleted} expenses, {categories_deleted} categories</p>
        </div>
        
        <a href="/demo-data/add/" class="btn">Add Demo Data Again</a>
    </body>
    </html>
    """
    
    return HttpResponse(html)
