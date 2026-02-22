from django.db import models
from django.conf import settings
import uuid

class SpendingInsight(models.Model):
    """AI-generated insights about user spending patterns"""
    
    INSIGHT_TYPES = [
        ('forecast', 'Spending Forecast'),
        ('anomaly', 'Unusual Spending'),
        ('trend', 'Spending Trend'),
        ('suggestion', 'Saving Suggestion'),
        ('risk', 'Budget Risk'),
    ]
    
    SEVERITY_LEVELS = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('danger', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='insights'
    )
    
    insight_type = models.CharField(max_length=20, choices=INSIGHT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='info')
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # Date range this insight applies to
    applies_to_month = models.IntegerField(null=True, blank=True)
    applies_to_year = models.IntegerField(null=True, blank=True)
    
    # Numerical data for visualization
    predicted_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    risk_score = models.IntegerField(null=True, blank=True)  # 0-100
    
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'insight_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_insight_type_display()}: {self.title}"
