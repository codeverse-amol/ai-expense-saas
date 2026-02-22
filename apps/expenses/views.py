from typing import cast
import calendar
import logging

from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.db.models import Sum, Q, Prefetch
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.core.cache import cache

from .models import Expense, MonthlyBudget, Category, CategoryBudget
from .forms import ExpenseForm, ExpenseFilterForm, CategoryForm, CategoryBudgetForm
from .budget_forms import MonthlyBudgetForm
from apps.ai_engine.ai_service import forecast_next_month_spending, generate_insights_for_user

import json

# Get logger for this module
logger = logging.getLogger(__name__)


# ======================================
# DASHBOARD VIEW
# ======================================
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "expenses/dashboard.html"
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        
        # Get year and month from query params or use current
        year = int(self.request.GET.get('year', now.year))
        month = int(self.request.GET.get('month', now.month))
        
        # Calculate previous and next month/year for navigation
        if month == 1:
            prev_month, prev_year = 12, year - 1
        else:
            prev_month, prev_year = month - 1, year
        
        if month == 12:
            next_month, next_year = 1, year + 1
        else:
            next_month, next_year = month + 1, year
        
        context['selected_year'] = year
        context['selected_month'] = month
        context['prev_year'] = prev_year
        context['prev_month'] = prev_month
        context['next_year'] = next_year
        context['next_month'] = next_month
        
        # Try to get cached dashboard data
        cache_key = f'dashboard_{user.id}_{year}_{month}'
        cached_data = cache.get(cache_key)
        
        if cached_data:
            logger.info(f"Dashboard cache hit for user {user.email}")
            # Update with navigation data
            cached_data.update({
                'selected_year': year,
                'selected_month': month,
                'prev_year': prev_year,
                'prev_month': prev_month,
                'next_year': next_year,
                'next_month': next_month,
            })
            context.update(cached_data)
            return context
        
        # Cache miss - calculate dashboard data
        logger.info(f"Dashboard cache miss for user {user.email}, calculating...")

        try:
            # Get basic stats with error handling
            total_spent = (
                Expense.objects.filter(user=user, is_deleted=False)
                .aggregate(total=Sum("amount"))["total"]
                or 0
            )

            monthly_spent = (
                Expense.objects.filter(
                    user=user,
                    is_deleted=False,
                    expense_date__year=year,
                    expense_date__month=month,
                )
                .aggregate(total=Sum("amount"))["total"]
                or 0
            )

            # Safe category data for selected month
            try:
                category_data = list(
                    Expense.objects.filter(
                        user=user, 
                        is_deleted=False,
                        expense_date__year=year,
                        expense_date__month=month
                    )
                    .values("category__name")
                    .annotate(total=Sum("amount"))
                )
            except:
                category_data = []

            # Budget info for selected month
            current_budget = MonthlyBudget.objects.filter(
                user=user,
                year=year,
                month=month
            ).first()

            budget_amount = current_budget.amount if current_budget else 0
            remaining_amount = budget_amount - monthly_spent
            percentage_used = (monthly_spent / budget_amount * 100) if budget_amount > 0 else 0
            
            # AI-powered forecast for next month
            predicted_next_month = forecast_next_month_spending(user)

            # Category-wise budget breakdown (optimized with prefetch)
            # Prefetch expenses for selected month to avoid N+1 queries
            current_month_expenses = Expense.objects.filter(
                user=user,
                is_deleted=False,
                expense_date__year=year,
                expense_date__month=month
            )
            
            category_budgets = CategoryBudget.objects.filter(
                user=user,
                year=year,
                month=month
            ).select_related('category').prefetch_related(
                Prefetch(
                    'category__expenses',
                    queryset=current_month_expenses,
                    to_attr='current_month_expenses'
                )
            )
            
            category_budget_data = []
            total_category_budget = 0
            
            for cat_budget in category_budgets:
                # Calculate spent from prefetched data (no extra query!)
                expenses_list = list(cat_budget.category.current_month_expenses)
                spent = sum(
                    expense.amount 
                    for expense in expenses_list
                )
                
                remaining = cat_budget.amount - spent
                percentage = (spent / cat_budget.amount * 100) if cat_budget.amount > 0 else 0
                
                category_budget_data.append({
                    'category': cat_budget.category,
                    'budget': cat_budget.amount,
                    'spent': spent,
                    'remaining': remaining,
                    'percentage': round(percentage, 1),
                    'status': 'danger' if percentage > 100 else ('warning' if percentage > 80 else 'success'),
                    'expenses': expenses_list  # Add expenses to show in dashboard
                })
                
                total_category_budget += cat_budget.amount

            # Calculate unallocated budget
            unallocated_budget = budget_amount - total_category_budget
            
            # Create date object for selected month
            from datetime import date
            selected_date = date(year, month, 1)

            
            # Cache the dashboard data for 15 minutes
            dashboard_data = {
                "total_spent": total_spent,
                "monthly_spent": monthly_spent,
                "category_data": category_data,
                "budget_amount": budget_amount,
                "remaining_amount": remaining_amount,
                "percentage_used": round(percentage_used, 2),
                "predicted_next_month": predicted_next_month,
                "category_budget_data": category_budget_data,
                "total_category_budget": total_category_budget,
                "unallocated_budget": unallocated_budget,
                "current_month": selected_date,  # First day of selected month for date formatting
                "current_year": year,
                "ai_insights": context.get("ai_insights", []),
            }
            cache.set(cache_key, dashboard_data, 60 * 15)  # 15 minutes
            logger.info(f"Dashboard data cached for user {user.email}")
            context["total_spent"] = total_spent
            context["monthly_spent"] = monthly_spent
            context["category_data"] = category_data
            context["budget_amount"] = budget_amount
            context["remaining_amount"] = remaining_amount
            context["percentage_used"] = round(percentage_used, 2)
            context["predicted_next_month"] = 0
            context["category_budget_data"] = category_budget_data
            context["total_category_budget"] = total_category_budget
            context["unallocated_budget"] = unallocated_budget
            
            from datetime import date
            selected_date = date(year, month, 1)
            context["current_month"] = selected_date  # First day of selected month for date formatting
            context["current_year"] = year

        except Exception as e:
            # If anything fails, just show empty dashboard
            logger.error(f"Dashboard error for user {user.email}: {e}", exc_info=True)
            from datetime import date
            selected_date = date(year, month, 1)
            context["total_spent"] = 0
            context["monthly_spent"] = 0
            context["category_data"] = []
            context["budget_amount"] = 0
            context["remaining_amount"] = 0
            context["percentage_used"] = 0
            context["predicted_next_month"] = 0
            context["category_budget_data"] = []
            context["total_category_budget"] = 0
            context["current_month"] = selected_date
            context["current_year"] = year

        return context


# ======================================
# EXPENSE LIST
# ======================================
class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = "expenses/expense_list.html"
    context_object_name = "expenses"
    login_url = 'login'
    paginate_by = 20

    def get_queryset(self):
        # Use select_related to avoid N+1 queries on category
        queryset = Expense.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).select_related('category')
        
        # Get filter parameters from GET request
        search = self.request.GET.get('search', '').strip()
        category_id = self.request.GET.get('category', '').strip()
        min_amount = self.request.GET.get('min_amount', '').strip()
        max_amount = self.request.GET.get('max_amount', '').strip()
        start_date = self.request.GET.get('start_date', '').strip()
        end_date = self.request.GET.get('end_date', '').strip()
        sort_by = self.request.GET.get('sort_by', '-expense_date').strip()
        
        # Apply search filter (search in title and notes)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(notes__icontains=search)
            )
        
        # Apply category filter
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Apply amount range filter
        if min_amount:
            try:
                queryset = queryset.filter(amount__gte=float(min_amount))
            except (ValueError, TypeError):
                pass
        
        if max_amount:
            try:
                queryset = queryset.filter(amount__lte=float(max_amount))
            except (ValueError, TypeError):
                pass
        
        # Apply date range filter
        if start_date:
            try:
                queryset = queryset.filter(expense_date__gte=start_date)
            except (ValueError, TypeError):
                pass
        
        if end_date:
            try:
                queryset = queryset.filter(expense_date__lte=end_date)
            except (ValueError, TypeError):
                pass
        
        # Apply sorting
        if sort_by in ['-expense_date', 'expense_date', '-amount', 'amount', 'title', '-title']:
            queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Create and populate the filter form
        filter_form = ExpenseFilterForm(user=self.request.user, data=self.request.GET)
        context['filter_form'] = filter_form
        
        # Add query string for maintaining filters in pagination
        context['query_string'] = self.request.GET.urlencode()
        
        # Count statistics
        total_expenses = Expense.objects.filter(
            user=self.request.user,
            is_deleted=False
        ).count()
        
        filtered_expenses = self.get_queryset().count()
        total_amount = self.get_queryset().aggregate(Sum('amount'))['amount__sum'] or 0
        
        context['total_expenses'] = total_expenses
        context['filtered_expenses'] = filtered_expenses
        context['total_amount'] = total_amount
        
        return context


# ======================================
# CREATE EXPENSE
# ======================================
class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    login_url = 'login'

    def get_success_url(self):
        # Check if 'next' parameter was passed
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse_lazy("expense-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_initial(self):
        """Pre-select category if passed in query parameter"""
        initial = super().get_initial()
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                # Verify the category belongs to the user
                category = Category.objects.get(id=category_id, user=self.request.user)
                initial['category'] = category
            except Category.DoesNotExist:
                pass
        return initial

    def form_valid(self, form):
        form.instance.user = self.request.user
        expense = form.save()
        
        # Invalidate dashboard cache
        now = timezone.now()
        cache_key = f'dashboard_{self.request.user.id}_{now.year}_{now.month}'
        cache.delete(cache_key)
        
        logger.info(f"User {self.request.user.email} created expense: {expense.title} - ₹{expense.amount}")
        return super().form_valid(form)


# ======================================
# UPDATE EXPENSE
# ======================================
class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expense-list")
    login_url = 'login'

    def get_queryset(self):
        return Expense.objects.filter(
            user=self.request.user,
            is_deleted=False
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        # Invalidate dashboard cache
        now = timezone.now()
        cache_key = f'dashboard_{self.request.user.id}_{now.year}_{now.month}'
        cache.delete(cache_key)
        return super().form_valid(form)


# ======================================
# SOFT DELETE EXPENSE
# ======================================
class ExpenseDeleteView(LoginRequiredMixin, UpdateView):
    model = Expense
    fields = []
    template_name = "expenses/expense_confirm_delete.html"
    success_url = reverse_lazy("expense-list")
    login_url = 'login'

    def get_queryset(self):
        return Expense.objects.filter(
            user=self.request.user,
            is_deleted=False
        )

    def post(self, request, *args, **kwargs):
        expense: Expense = cast(Expense, self.get_object())
        
        # Invalidate dashboard cache
        now = timezone.now()
        cache_key = f'dashboard_{request.user.id}_{now.year}_{now.month}'
        cache.delete(cache_key)
        
        logger.info(f"User {request.user.email} soft-deleted expense: {expense.title} - ₹{expense.amount}")
        expense.is_deleted = True
        expense.save()
        return redirect("expense-list")


# ======================================
# CREATE MONTHLY BUDGET
# ======================================
class MonthlyBudgetCreateView(LoginRequiredMixin, CreateView):
    model = MonthlyBudget
    form_class = MonthlyBudgetForm
    template_name = "expenses/budget_form.html"
    success_url = reverse_lazy("dashboard")
    login_url = 'login'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Invalidate dashboard cache
        now = timezone.now()
        cache_key = f'dashboard_{self.request.user.id}_{now.year}_{now.month}'
        cache.delete(cache_key)
        
        logger.info(f"User {self.request.user.email} created budget: ₹{form.instance.amount} for {form.instance.year}/{form.instance.month}")
        return super().form_valid(form)


class MonthlyBudgetUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing monthly budget"""
    model = MonthlyBudget
    form_class = MonthlyBudgetForm
    template_name = "expenses/budget_form.html"
    success_url = reverse_lazy("budget-history")
    login_url = 'login'

    def get_queryset(self):
        return MonthlyBudget.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        kwargs["is_edit"] = True  # Flag to skip duplicate check
        return kwargs

    def form_valid(self, form):
        # Invalidate dashboard cache for this budget's month
        cache_key = f'dashboard_{self.request.user.id}_{form.instance.year}_{form.instance.month}'
        cache.delete(cache_key)
        
        logger.info(f"User {self.request.user.email} updated budget: ₹{form.instance.amount} for {form.instance.year}/{form.instance.month}")
        return super().form_valid(form)
        
        # Invalidate dashboard cache
        now = timezone.now()
        cache_key = f'dashboard_{self.request.user.id}_{now.year}_{now.month}'
        cache.delete(cache_key)
        
        return super().form_valid(form)
    




class BudgetHistoryView(LoginRequiredMixin, ListView):
    model = MonthlyBudget
    template_name = "expenses/budget_history.html"
    context_object_name = "budgets"
    login_url = 'login'

    def get_queryset(self):
        queryset = MonthlyBudget.objects.filter(user=self.request.user)
        
        # Get year filter from query params
        year_filter = self.request.GET.get('year')
        if year_filter and year_filter != 'all':
            queryset = queryset.filter(year=int(year_filter))
        
        return queryset.order_by("-year", "-month")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        budgets = context["budgets"]

        budget_data = []

        for budget in budgets:
            monthly_spent = (
                Expense.objects.filter(
                    user=self.request.user,
                    is_deleted=False,
                    expense_date__year=budget.year,
                    expense_date__month=budget.month,
                )
                .aggregate(total=Sum("amount"))["total"]
                or 0
            )

            remaining = budget.amount - monthly_spent

            budget_data.append({
                "id": budget.id,
                "year": budget.year,
                "month": budget.month,
                "month_name": calendar.month_name[budget.month],
                "budget_amount": budget.amount,
                "spent": monthly_spent,
                "remaining": remaining,
                "exceeded": monthly_spent > budget.amount
            })

        context["budget_data"] = budget_data
        
        # Get distinct years for the dropdown
        all_budgets = MonthlyBudget.objects.filter(user=self.request.user)
        years = sorted(set(b.year for b in all_budgets), reverse=True)
        context["available_years"] = years
        context["selected_year"] = self.request.GET.get('year', 'all')

        months = []
        budget_values = []
        spent_values = []

        for item in budget_data:
            months.append(f"{item['month']}/{item['year']}")
            budget_values.append(float(item["budget_amount"]))
            spent_values.append(float(item["spent"]))

        context["chart_months"] = json.dumps(months[::-1])
        context["chart_budget"] = json.dumps(budget_values[::-1])
        context["chart_spent"] = json.dumps(spent_values[::-1])
        return context


class MonthlyBudgetDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a monthly budget"""
    model = MonthlyBudget
    template_name = "expenses/budget_confirm_delete.html"
    success_url = reverse_lazy("budget-history")
    login_url = 'login'

    def get_queryset(self):
        return MonthlyBudget.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        """Override delete to also remove category budgets"""
        budget = self.get_object()
        
        # Invalidate dashboard cache for this budget's month
        cache_key = f'dashboard_{request.user.id}_{budget.year}_{budget.month}'
        cache.delete(cache_key)
        
        # Also delete associated category budgets for this month
        CategoryBudget.objects.filter(
            user=request.user,
            year=budget.year,
            month=budget.month
        ).delete()
        return super().delete(request, *args, **kwargs)


# ======================================
# CATEGORY MANAGEMENT
# ======================================
class CategoryListView(LoginRequiredMixin, ListView):
    """List all categories for the current user"""
    model = Category
    template_name = "expenses/category_list.html"
    context_object_name = "categories"
    login_url = 'login'

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        
        # Get year and month from query params or use current
        year = int(self.request.GET.get('year', now.year))
        month = int(self.request.GET.get('month', now.month))
        
        # Get available years for filter
        budget_years = MonthlyBudget.objects.filter(user=user).values_list('year', flat=True).distinct().order_by('-year')
        available_years = list(budget_years) if budget_years else [now.year]
        if year not in available_years:
            available_years.append(year)
            available_years.sort(reverse=True)
        
        # Month name for display
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        month_name = month_names[month - 1]
        
        # Get category budgets for selected month
        category_budgets = {}
        for cb in CategoryBudget.objects.filter(user=user, year=year, month=month):
            category_budgets[cb.category_id] = cb.amount
        
        # Get expenses per category for selected month
        category_expenses = {}
        expenses = Expense.objects.filter(
            user=user,
            expense_date__year=year,
            expense_date__month=month,
            is_deleted=False
        )
        for expense in expenses:
            if expense.category_id not in category_expenses:
                category_expenses[expense.category_id] = 0
            category_expenses[expense.category_id] += expense.amount
        
        # Attach budget and expense data to categories
        categories_data = []
        for category in self.get_queryset():
            budget = category_budgets.get(category.id, 0)
            spent = category_expenses.get(category.id, 0)
            categories_data.append({
                'category': category,
                'budget': budget,
                'spent': spent,
                'remaining': budget - spent,
                'percentage': round((spent / budget * 100), 1) if budget > 0 else 0
            })
        
        context['categories_data'] = categories_data
        context['year'] = year
        context['month'] = month
        context['month_name'] = month_name
        context['available_years'] = available_years
        
        return context


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new category"""
    model = Category
    form_class = CategoryForm
    template_name = "expenses/category_form.html"
    login_url = 'login'

    def get_success_url(self):
        # Check if 'next' parameter was passed
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        return reverse_lazy("category-list")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing category"""
    model = Category
    form_class = CategoryForm
    template_name = "expenses/category_form.html"
    success_url = reverse_lazy("category-list")
    login_url = 'login'

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)


class CategoryDeleteView(LoginRequiredMixin, UpdateView):
    """Delete a category"""
    model = Category
    template_name = "expenses/category_confirm_delete.html"
    success_url = reverse_lazy("category-list")
    login_url = 'login'

    def get_queryset(self):
        return Category.objects.filter(user=self.request.user)

    def post(self, request, *args, **kwargs):
        category: Category = cast(Category, self.get_object())
        # Check if category is being used by any expenses
        expense_count = Expense.objects.filter(
            category=category,
            is_deleted=False
        ).count()
        
        if expense_count > 0:
            # Redirect back with error message (you can add messages framework)
            return redirect("category-list")
        
        category.delete()
        return redirect("category-list")


# ======================================
# CATEGORY BUDGET MANAGEMENT
# ======================================
class CategoryBudgetSetupView(LoginRequiredMixin, TemplateView):
    """View to set budgets for all categories for current month"""
    template_name = "expenses/category_budget_setup.html"
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()
        
        # Get year and month from query params or use current
        year = int(self.request.GET.get('year', now.year))
        month = int(self.request.GET.get('month', now.month))
        
        # Get all user's categories
        categories = Category.objects.filter(user=user)
        
        # Get existing category budgets for this month
        existing_budgets = {}
        category_budgets = CategoryBudget.objects.filter(
            user=user,
            year=year,
            month=month
        )
        for cb in category_budgets:
            existing_budgets[cb.category_id] = cb.amount
        
        # Prepare category data with current budgets
        category_data = []
        for category in categories:
            category_data.append({
                'id': category.id,
                'name': category.name,
                'current_budget': existing_budgets.get(category.id, 0)
            })
        
        # Get monthly budget if exists
        monthly_budget = MonthlyBudget.objects.filter(
            user=user,
            year=year,
            month=month
        ).first()
        
        # Get available years for filter
        budget_years = MonthlyBudget.objects.filter(user=user).values_list('year', flat=True).distinct().order_by('-year')
        available_years = list(budget_years) if budget_years else [now.year]
        if year not in available_years:
            available_years.append(year)
            available_years.sort(reverse=True)
        
        # Month name for display
        month_names = ['January', 'February', 'March', 'April', 'May', 'June',
                      'July', 'August', 'September', 'October', 'November', 'December']
        month_name = month_names[month - 1]
        
        context['categories'] = category_data
        context['year'] = year
        context['month'] = month
        context['month_name'] = month_name
        context['monthly_budget'] = monthly_budget
        context['total_allocated'] = sum(existing_budgets.values())
        context['available_years'] = available_years
        context['is_current_month'] = (year == now.year and month == now.month)
        
        return context
    
    def post(self, request, *args, **kwargs):
        user = request.user
        now = timezone.now()
        
        year = int(request.POST.get('year', now.year))
        month = int(request.POST.get('month', now.month))
        
        # Process each category budget
        categories = Category.objects.filter(user=user)
        for category in categories:
            amount_key = f'budget_{category.id}'
            amount = request.POST.get(amount_key, '0').strip()
            
            if amount and float(amount) > 0:
                # Update or create category budget
                CategoryBudget.objects.update_or_create(
                    user=user,
                    category=category,
                    year=year,
                    month=month,
                    defaults={'amount': float(amount)}
                )
            else:
                # Delete if amount is 0 or empty
                CategoryBudget.objects.filter(
                    user=user,
                    category=category,
                    year=year,
                    month=month
                ).delete()
        
        # Invalidate dashboard cache
        cache_key = f'dashboard_{user.id}_{year}_{month}'
        cache.delete(cache_key)
        
        return redirect('dashboard')