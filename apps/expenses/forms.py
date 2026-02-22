from django import forms
from .models import Expense, Category, MonthlyBudget, CategoryBudget


class CategoryForm(forms.ModelForm):
    """Form for creating and editing categories"""
    class Meta:
        model = Category
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter category name (e.g., Food, Transport, Bills)"
            })
        }


class CategoryBudgetForm(forms.ModelForm):
    """Form for setting budget for a category in a specific month"""
    class Meta:
        model = CategoryBudget
        fields = ["category", "amount"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "placeholder": "Enter budget amount",
                "step": "0.01",
                "min": "0"
            })
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["title", "amount", "category", "expense_date", "notes"]
        widgets = {
            "expense_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)  # Get user from kwargs
        super().__init__(*args, **kwargs)
        
        # Filter category queryset to only show user's categories
        if user:
            self.fields['category'].queryset = Category.objects.filter(user=user)


class ExpenseFilterForm(forms.Form):
    """Filter form for expenses"""
    search = forms.CharField(
        required=False,
        label="Search",
        widget=forms.TextInput(attrs={
            "placeholder": "Search by title or notes...",
            "class": "form-control"
        })
    )
    
    category = forms.ModelChoiceField(
        required=False,
        queryset=Category.objects.none(),
        label="Category",
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )
    
    min_amount = forms.DecimalField(
        required=False,
        label="Minimum Amount",
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "placeholder": "Min amount",
            "class": "form-control",
            "step": "0.01"
        })
    )
    
    max_amount = forms.DecimalField(
        required=False,
        label="Maximum Amount",
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "placeholder": "Max amount",
            "class": "form-control",
            "step": "0.01"
        })
    )
    
    start_date = forms.DateField(
        required=False,
        label="Start Date",
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "form-control"
        })
    )
    
    end_date = forms.DateField(
        required=False,
        label="End Date",
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "form-control"
        })
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        initial="-expense_date",
        choices=[
            ("-expense_date", "Newest First"),
            ("expense_date", "Oldest First"),
            ("-amount", "Highest Amount"),
            ("amount", "Lowest Amount"),
            ("title", "Title (A-Z)"),
            ("-title", "Title (Z-A)"),
        ],
        label="Sort By",
        widget=forms.Select(attrs={
            "class": "form-select"
        })
    )
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set available categories for the user only if user is provided
        if user:
            try:
                self.fields['category'].queryset = Category.objects.filter(
                    user=user
                ).order_by('name')
            except Exception as e:
                print(f"Error loading categories: {e}")
                self.fields['category'].queryset = Category.objects.none()