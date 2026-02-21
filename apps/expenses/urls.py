from django.urls import path
from .views import (
    DashboardView,
    ExpenseListView,
    ExpenseCreateView,
    ExpenseUpdateView,
    ExpenseDeleteView,
    MonthlyBudgetCreateView,
    BudgetHistoryView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("expenses/", ExpenseListView.as_view(), name="expense-list"),
    path("add/", ExpenseCreateView.as_view(), name="expense-add"),
    path("edit/<uuid:pk>/", ExpenseUpdateView.as_view(), name="expense-edit"),
    path("delete/<uuid:pk>/", ExpenseDeleteView.as_view(), name="expense-delete"),
    path("budget/add/", MonthlyBudgetCreateView.as_view(), name="budget-add"),
    path("budgets/history/", BudgetHistoryView.as_view(), name="budget-history"),
]