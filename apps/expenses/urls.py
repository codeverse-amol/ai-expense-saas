from django.urls import path
from .views import (
    DashboardView,
    ExpenseListView,
    ExpenseCreateView,
    ExpenseUpdateView,
    ExpenseDeleteView,
    MonthlyBudgetCreateView,
    BudgetHistoryView,
    CategoryListView,
    CategoryCreateView,
    CategoryUpdateView,
    CategoryDeleteView,
    CategoryBudgetSetupView,
)

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("expenses/", ExpenseListView.as_view(), name="expense-list"),
    path("add/", ExpenseCreateView.as_view(), name="expense-add"),
    path("edit/<uuid:pk>/", ExpenseUpdateView.as_view(), name="expense-edit"),
    path("delete/<uuid:pk>/", ExpenseDeleteView.as_view(), name="expense-delete"),
    path("budget/add/", MonthlyBudgetCreateView.as_view(), name="budget-add"),
    path("budgets/history/", BudgetHistoryView.as_view(), name="budget-history"),
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/add/", CategoryCreateView.as_view(), name="category-add"),
    path("categories/edit/<uuid:pk>/", CategoryUpdateView.as_view(), name="category-edit"),
    path("categories/delete/<uuid:pk>/", CategoryDeleteView.as_view(), name="category-delete"),
    path("category-budgets/setup/", CategoryBudgetSetupView.as_view(), name="category-budget-setup"),
]