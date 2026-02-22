from django.contrib import admin
from .models import SpendingInsight


@admin.register(SpendingInsight)
class SpendingInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'insight_type', 'severity', 'title', 'created_at', 'is_read']
    list_filter = ['insight_type', 'severity', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'
