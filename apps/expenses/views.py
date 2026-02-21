from typing import cast

from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone

from .models import Expense, MonthlyBudget
from .forms import ExpenseForm
from .budget_forms import MonthlyBudgetForm

import json


# ======================================
# DASHBOARD VIEW
# ======================================
class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "expenses/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        # -----------------------------
        # TOTAL SPENDING
        # -----------------------------
        total_spent = (
            Expense.objects.filter(user=user, is_deleted=False)
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

        # -----------------------------
        # CURRENT MONTH SPENDING
        # -----------------------------
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

        # -----------------------------
        # CATEGORY BREAKDOWN
        # -----------------------------
        category_data = (
            Expense.objects.filter(user=user, is_deleted=False)
            .values("category__name")
            .annotate(total=Sum("amount"))
        )

        # -----------------------------
        # MONTHLY TREND DATA (Prediction)
        # -----------------------------
        monthly_data = (
            Expense.objects.filter(user=user, is_deleted=False)
            .annotate(month=TruncMonth("expense_date"))
            .values("month")
            .annotate(total=Sum("amount"))
            .order_by("month")
        )

        monthly_totals = [item["total"] for item in monthly_data]

        if len(monthly_totals) >= 3:
            predicted_next_month = sum(monthly_totals[-3:]) / 3
        elif monthly_totals:
            predicted_next_month = sum(monthly_totals) / len(monthly_totals)
        else:
            predicted_next_month = 0

        # -----------------------------
        # CURRENT MONTH BUDGET
        # -----------------------------
        current_budget = MonthlyBudget.objects.filter(
            user=user,
            year=now.year,
            month=now.month
        ).first()

        if current_budget:
            budget_amount = current_budget.amount
        else:
            budget_amount = 0

        # Remaining amount
        remaining_amount = budget_amount - monthly_spent

        # Percentage used
        if budget_amount > 0:
            percentage_used = (monthly_spent / budget_amount) * 100
        else:
            percentage_used = 0

        # -----------------------------
        # CONTEXT
        # -----------------------------
        context["total_spent"] = total_spent
        context["monthly_spent"] = monthly_spent
        context["category_data"] = list(category_data)
        context["predicted_next_month"] = round(predicted_next_month, 2)

        context["budget_amount"] = budget_amount
        context["remaining_amount"] = remaining_amount
        context["percentage_used"] = round(percentage_used, 2)

        # SMART INSIGHTS
        insights = []

        # Compare this month vs last month
        last_month = now.month - 1
        last_year = now.year

        if last_month == 0:
            last_month = 12
            last_year -= 1

        last_month_spent = (
            Expense.objects.filter(
                user=user,
                is_deleted=False,
                expense_date__year=last_year,
                expense_date__month=last_month,
            )
            .aggregate(total=Sum("amount"))["total"]
            or 0
        )

        if last_month_spent > 0:
            difference = monthly_spent - last_month_spent
            percent_change = (difference / last_month_spent) * 100

            if percent_change > 0:
                insights.append(
                    f"You are spending {round(percent_change,2)}% more than last month."
                )
            elif percent_change < 0:
                insights.append(
                    f"Great job! You reduced spending by {abs(round(percent_change,2))}% compared to last month."
                )

        # Highest category
        category_list = list(category_data)

        if category_list:
            highest_category = max(category_list, key=lambda x: x["total"])
            insights.append(
                f"Your highest spending category is {highest_category['category__name']}."
            )

        # Budget risk
        if budget_amount > 0 and predicted_next_month > budget_amount:
            insights.append(
                "Warning: Based on trends, you may exceed next month's budget."
            )

        context["insights"] = insights

        return context


# ======================================
# EXPENSE LIST
# ======================================
class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = "expenses/expense_list.html"
    context_object_name = "expenses"

    def get_queryset(self):
        return Expense.objects.filter(
            user=self.request.user,
            is_deleted=False
        )


# ======================================
# CREATE EXPENSE
# ======================================
class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = "expenses/expense_form.html"
    success_url = reverse_lazy("expense-list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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