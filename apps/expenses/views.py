from typing import cast

from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import Expense, MonthlyBudget, Category, CategoryBudget
from .forms import ExpenseForm, ExpenseFilterForm, CategoryForm, CategoryBudgetForm
from .budget_forms import MonthlyBudgetForm

import json


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
                    expense_date__year=now.year,
                    expense_date__month=now.month,
                )
                .aggregate(total=Sum("amount"))["total"]
                or 0
            )

            # Safe category data
            try:
                category_data = list(
                    Expense.objects.filter(user=user, is_deleted=False)
                    .values("category__name")
                    .annotate(total=Sum("amount"))
                )
            except:
                category_data = []

            # Budget info
            current_budget = MonthlyBudget.objects.filter(
                user=user,
                year=now.year,
                month=now.month
            ).first()

            budget_amount = current_budget.amount if current_budget else 0
            remaining_amount = budget_amount - monthly_spent
            percentage_used = (monthly_spent / budget_amount * 100) if budget_amount > 0 else 0

            # Category-wise budget breakdown
            category_budgets = CategoryBudget.objects.filter(
                user=user,
                year=now.year,
                month=now.month
            ).select_related('category')
            
            category_budget_data = []
            total_category_budget = 0
            
            for cat_budget in category_budgets:
                # Calculate spent for this category this month
                spent = Expense.objects.filter(
                    user=user,
                    category=cat_budget.category,
                    is_deleted=False,
                    expense_date__year=now.year,
                    expense_date__month=now.month
                ).aggregate(total=Sum("amount"))["total"] or 0
                
                remaining = cat_budget.amount - spent
                percentage = (spent / cat_budget.amount * 100) if cat_budget.amount > 0 else 0
                
                category_budget_data.append({
                    'category': cat_budget.category,
                    'budget': cat_budget.amount,
                    'spent': spent,
                    'remaining': remaining,
                    'percentage': round(percentage, 1),
                    'status': 'danger' if percentage > 100 else ('warning' if percentage > 80 else 'success')
                })
                
                total_category_budget += cat_budget.amount

            context["total_spent"] = total_spent
            context["monthly_spent"] = monthly_spent
            context["category_data"] = category_data
            context["budget_amount"] = budget_amount
            context["remaining_amount"] = remaining_amount
            context["percentage_used"] = round(percentage_used, 2)
            context["predicted_next_month"] = 0
            context["category_budget_data"] = category_budget_data
            context["total_category_budget"] = total_category_budget
            context["current_month"] = now.month
            context["current_year"] = now.year

        except Exception as e:
            # If anything fails, just show empty dashboard
            print(f"[ERROR] Dashboard error: {e}")
            context["total_spent"] = 0
            context["monthly_spent"] = 0
            context["category_data"] = []
            context["budget_amount"] = 0
            context["remaining_amount"] = 0
            context["percentage_used"] = 0
            context["predicted_next_month"] = 0
            context["category_budget_data"] = []
            context["total_category_budget"] = 0

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
        queryset = Expense.objects.filter(
            user=self.request.user,
            is_deleted=False
        )
        
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
    success_url = reverse_lazy("expense-list")
    login_url = 'login'

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
        return super().form_valid(form)
    




class BudgetHistoryView(LoginRequiredMixin, ListView):
    model = MonthlyBudget
    template_name = "expenses/budget_history.html"
    context_object_name = "budgets"
    login_url = 'login'

    def get_queryset(self):
        return MonthlyBudget.objects.filter(
            user=self.request.user
        ).order_by("-year", "-month")

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
                "year": budget.year,
                "month": budget.month,
                "budget_amount": budget.amount,
                "spent": monthly_spent,
                "remaining": remaining,
                "exceeded": monthly_spent > budget.amount
            })

        context["budget_data"] = budget_data

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


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new category"""
    model = Category
    form_class = CategoryForm
    template_name = "expenses/category_form.html"
    success_url = reverse_lazy("category-list")
    login_url = 'login'

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
        
        context['categories'] = category_data
        context['year'] = year
        context['month'] = month
        context['monthly_budget'] = monthly_budget
        context['total_allocated'] = sum(existing_budgets.values())
        
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
        
        return redirect('dashboard')