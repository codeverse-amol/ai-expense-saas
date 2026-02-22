from django.db import models
from django.conf import settings
import uuid

class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories"
    )

    name = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.user.email})"
    

class CategoryBudget(models.Model):
    """Budget allocation for a specific category in a specific month"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="category_budgets"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="budgets"
    )

    year = models.IntegerField()
    month = models.IntegerField()  # 1-12

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "category", "year", "month")
        ordering = ["category__name"]
        indexes = [
            models.Index(fields=["user", "year", "month"]),
            models.Index(fields=["category", "year", "month"]),
        ]

    def __str__(self):
        return f"{self.category.name}: {self.amount} ({self.month}/{self.year})"


class Expense(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    expense_date = models.DateField()

    notes = models.TextField(blank=True, null=True)

    is_deleted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-expense_date"]
        indexes = [
            models.Index(fields=["user", "expense_date"]),
            models.Index(fields=["user", "category", "expense_date"]),
            models.Index(fields=["user", "is_deleted", "expense_date"]),
            models.Index(fields=["expense_date", "category"]),  # For aggregations
        ]

    def __str__(self):
        return f"{self.title} - {self.amount}"





class MonthlyBudget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budgets"
    )

    year = models.IntegerField()
    month = models.IntegerField()  # 1-12

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "year", "month")
        ordering = ["-year", "-month"]
        indexes = [
            models.Index(fields=["user", "year", "month"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.month}/{self.year}"