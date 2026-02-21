from django import forms
from .models import MonthlyBudget
from django.utils import timezone


class MonthlyBudgetForm(forms.ModelForm):

    class Meta:
        model = MonthlyBudget
        fields = ["year", "month", "amount"]

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        current_year = timezone.now().year
        self.fields["year"].initial = current_year
        self.fields["month"].initial = timezone.now().month

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get("year")
        month = cleaned_data.get("month")

        if MonthlyBudget.objects.filter(
            user=self.user,
            year=year,
            month=month
        ).exists():
            raise forms.ValidationError("Budget already exists for this month.")

        return cleaned_data