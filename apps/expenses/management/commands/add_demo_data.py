"""
Management command to add demo data for testing AI insights
Usage: python manage.py add_demo_data --user=email@example.com
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from apps.expenses.models import Expense, Category, MonthlyBudget, CategoryBudget

User = get_user_model()


class Command(BaseCommand):
    help = 'Add demo expense data for AI insights testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Email of the user to add data for',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before adding new',
        )

    def handle(self, *args, **options):
        user_email = options.get('user')
        clear_data = options.get('clear', False)

        # Get user
        if user_email:
            try:
                user = User.objects.get(email=user_email)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {user_email} not found'))
                return
        else:
            users = User.objects.all()
            if not users.exists():
                self.stdout.write(self.style.ERROR('No users found. Create a user first.'))
                return
            user = users.first()

        self.stdout.write(self.style.SUCCESS(f'Adding demo data for: {user.email}'))

        # Clear existing data if requested
        if clear_data:
            self.stdout.write('Clearing existing data...')
            Expense.objects.filter(user=user).delete()
            CategoryBudget.objects.filter(user=user).delete()
            MonthlyBudget.objects.filter(user=user).delete()
            Category.objects.filter(user=user).delete()

        # Create categories
        categories_data = [
            ('Food & Dining', ['Breakfast', 'Lunch', 'Dinner', 'Groceries', 'Snacks']),
            ('Transport', ['Gas', 'Metro', 'Uber', 'Parking', 'Auto']),
            ('Entertainment', ['Movies', 'Gaming', 'Streaming', 'Concert', 'Sports']),
            ('Shopping', ['Clothes', 'Electronics', 'Books', 'Gadgets', 'Shoes']),
            ('Bills & Utilities', ['Internet', 'Electricity', 'Water', 'Phone', 'Gas Bill']),
        ]

        self.stdout.write('Creating categories...')
        created_categories = {}

        for cat_name, _ in categories_data:
            category, created = Category.objects.get_or_create(
                user=user,
                name=cat_name
            )
            created_categories[cat_name] = category
            status = "Created" if created else "Exists"
            self.stdout.write(f'  {status}: {cat_name}')

        # Create monthly budget
        now = timezone.now()
        self.stdout.write('Creating monthly budget...')
        budget, created = MonthlyBudget.objects.get_or_create(
            user=user,
            year=now.year,
            month=now.month,
            defaults={'amount': Decimal('50000.00')}
        )
        self.stdout.write(f'  Budget: ₹50,000 for {now.strftime("%B %Y")}')

        # Create category budgets
        category_budgets = {
            'Food & Dining': Decimal('15000.00'),
            'Transport': Decimal('8000.00'),
            'Entertainment': Decimal('5000.00'),
            'Shopping': Decimal('10000.00'),
            'Bills & Utilities': Decimal('7000.00'),
        }

        self.stdout.write('Creating category budgets...')
        for cat_name, amount in category_budgets.items():
            if cat_name in created_categories:
                CategoryBudget.objects.get_or_create(
                    user=user,
                    category=created_categories[cat_name],
                    year=now.year,
                    month=now.month,
                    defaults={'amount': amount}
                )
                self.stdout.write(f'  {cat_name}: ₹{amount}')

        # Add expenses for last 3 months
        self.stdout.write('Adding expenses...')
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

        self.stdout.write(self.style.SUCCESS(f'\n✓ Added {expenses_added} expenses'))
        self.stdout.write(self.style.SUCCESS('✓ Demo data setup complete!'))
        self.stdout.write('\nNext: Visit /dashboard/ to see AI insights')
