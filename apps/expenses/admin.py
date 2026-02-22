from django.contrib import admin
from .models import Category, Expense, CategoryBudget, MonthlyBudget


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "created_at")


@admin.register(CategoryBudget)
class CategoryBudgetAdmin(admin.ModelAdmin):
    list_display = ("category", "user", "amount", "month", "year", "created_at")
    list_filter = ("year", "month", "category")
    search_fields = ("category__name", "user__email")


@admin.register(MonthlyBudget)
class MonthlyBudgetAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "month", "year", "created_at")
    list_filter = ("year", "month")
    search_fields = ("user__email",)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ("title", "amount", "category", "user", "expense_date")
    list_filter = ("category", "expense_date")
    search_fields = ("title",)