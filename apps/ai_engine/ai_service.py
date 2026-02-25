"""
AI Service Module - Forecasting and Insights Generation
"""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional

import numpy as np
import pandas as pd
from django.db.models import Sum, Avg
from django.utils import timezone

from apps.expenses.models import Expense, Category, CategoryBudget, MonthlyBudget
from .models import SpendingInsight

logger = logging.getLogger(__name__)


def forecast_next_month_spending(user) -> Decimal:
    """
    Simple moving average forecast for next month's spending
    Uses last 3 months of data
    """
    try:
        now = timezone.now()
        
        # Get last 3 months of spending
        spending_by_month = []
        for i in range(1, 4):  # Last 3 months
            month_date = now - timedelta(days=30 * i)
            month_total = Expense.objects.filter(
                user=user,
                is_deleted=False,
                expense_date__year=month_date.year,
                expense_date__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            spending_by_month.append(float(month_total))
        
        # Calculate moving average
        if spending_by_month:
            forecast = sum(spending_by_month) / len(spending_by_month)
            logger.info(f"Forecast for user {user.email}: ₹{forecast:.2f}")
            return Decimal(str(round(forecast, 2)))
        
        return Decimal('0.00')
        
    except Exception as e:
        logger.error(f"Forecast error for user {user.email}: {e}")
        return Decimal('0.00')


def detect_spending_anomalies(user, month: int = None, year: int = None) -> List[Dict]:
    """
    Detect unusual spending transactions using statistical methods
    Returns list of anomalous expenses
    """
    try:
        now = timezone.now()
        month = month or now.month
        year = year or now.year
        
        # Get all expenses for the month
        expenses = Expense.objects.filter(
            user=user,
            is_deleted=False,
            expense_date__year=year,
            expense_date__month=month
        ).values('id', 'title', 'amount', 'category__name', 'expense_date')
        
        if not expenses:
            return []
        
        # Calculate statistics
        amounts = [float(e['amount']) for e in expenses]
        mean = np.mean(amounts)
        std = np.std(amounts)
        
        # Flag transactions > 2 standard deviations from mean
        anomalies = []
        threshold = mean + (2 * std)
        
        for expense in expenses:
            if float(expense['amount']) > threshold:
                anomalies.append({
                    'expense_id': expense['id'],
                    'title': expense['title'],
                    'amount': expense['amount'],
                    'category': expense['category__name'],
                    'date': expense['expense_date'],
                    'deviation': float(expense['amount']) - mean
                })
        
        logger.info(f"Found {len(anomalies)} anomalies for user {user.email}")
        return anomalies
        
    except Exception as e:
        logger.error(f"Anomaly detection error: {e}")
        return []


def calculate_budget_risk_score(user, month: int = None, year: int = None) -> int:
    """
    Calculate risk score (0-100) of exceeding budget
    Based on current spending pace and days remaining
    """
    try:
        now = timezone.now()
        month = month or now.month
        year = year or now.year
        
        # Get monthly budget
        budget = MonthlyBudget.objects.filter(
            user=user,
            year=year,
            month=month
        ).first()
        
        if not budget:
            return 0
        
        # Get current spending
        current_spending = Expense.objects.filter(
            user=user,
            is_deleted=False,
            expense_date__year=year,
            expense_date__month=month
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # Calculate days elapsed and remaining
        days_in_month = 30  # Simplified
        current_day = now.day
        days_elapsed = current_day
        days_remaining = days_in_month - days_elapsed
        
        if days_elapsed == 0:
            return 0
        
        # Calculate daily burn rate
        daily_burn_rate = float(current_spending) / days_elapsed
        
        # Project end-of-month spending
        projected_spending = float(current_spending) + (daily_burn_rate * days_remaining)
        
        # Calculate percentage of budget
        percentage = (projected_spending / float(budget.amount)) * 100
        
        # Risk score: 0-49 = low, 50-79 = medium, 80-100 = high
        if percentage <= 80:
            risk_score = int(percentage * 0.5)  # Map to 0-40
        elif percentage <= 100:
            risk_score = int(40 + ((percentage - 80) * 2))  # Map to 40-80
        else:
            risk_score = min(100, int(80 + ((percentage - 100) * 0.5)))  # Map to 80-100
        
        logger.info(f"Budget risk score for user {user.email}: {risk_score}")
        return risk_score
        
    except Exception as e:
        logger.error(f"Risk calculation error: {e}")
        return 0


def analyze_category_trends(user, category, months: int = 3) -> Dict:
    """
    Analyze spending trends for a specific category
    Returns trend direction and percentage change
    """
    try:
        now = timezone.now()
        monthly_totals = []
        
        for i in range(months):
            month_date = now - timedelta(days=30 * i)
            total = Expense.objects.filter(
                user=user,
                category=category,
                is_deleted=False,
                expense_date__year=month_date.year,
                expense_date__month=month_date.month
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            monthly_totals.append(float(total))
        
        if len(monthly_totals) < 2:
            return {'trend': 'stable', 'change': 0}
        
        # Simple trend: compare first and last month
        recent = monthly_totals[0]
        older = monthly_totals[-1]
        
        if older == 0:
            return {'trend': 'new', 'change': 100}
        
        change_pct = ((recent - older) / older) * 100
        
        if change_pct > 10:
            trend = 'increasing'
        elif change_pct < -10:
            trend = 'decreasing'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change': round(change_pct, 1),
            'recent_amount': recent,
            'older_amount': older
        }
        
    except Exception as e:
        logger.error(f"Category trend analysis error: {e}")
        return {'trend': 'unknown', 'change': 0}


def generate_insights_for_user(user) -> List[SpendingInsight]:
    """
    Generate all AI insights for a user
    Called periodically (daily) or on-demand
    """
    insights = []
    now = timezone.now()
    
    try:
        # Clear old insights (keep last 30 days)
        SpendingInsight.objects.filter(
            user=user,
            created_at__lt=now - timedelta(days=30)
        ).delete()
        
        # 1. Next month forecast
        forecast = forecast_next_month_spending(user)
        if forecast > 0:
            insight = SpendingInsight.objects.create(
                user=user,
                insight_type='forecast',
                severity='info',
                title=f'Next Month Forecast: ₹{forecast}',
                message=f'Based on your last 3 months, you\'re likely to spend ₹{forecast} next month.',
                predicted_amount=forecast,
                applies_to_month=(now.month % 12) + 1,
                applies_to_year=now.year if now.month < 12 else now.year + 1
            )
            insights.append(insight)
        
        # 2. Budget risk assessment
        risk_score = calculate_budget_risk_score(user)
        if risk_score > 50:
            severity = 'danger' if risk_score > 80 else 'warning'
            insight = SpendingInsight.objects.create(
                user=user,
                insight_type='risk',
                severity=severity,
                title=f'Budget Risk: {risk_score}% likelihood of overspending',
                message=f'At your current pace, you have a {risk_score}% chance of exceeding your budget this month.',
                risk_score=risk_score,
                applies_to_month=now.month,
                applies_to_year=now.year
            )
            insights.append(insight)
        
        # 3. Anomaly detection
        anomalies = detect_spending_anomalies(user)
        if anomalies:
            for anomaly in anomalies[:3]:  # Top 3 anomalies
                insight = SpendingInsight.objects.create(
                    user=user,
                    insight_type='anomaly',
                    severity='warning',
                    title=f'Unusual expense detected: ₹{anomaly["amount"]}',
                    message=f'{anomaly["title"]} (₹{anomaly["amount"]}) is significantly higher than your average.',
                    actual_amount=anomaly['amount'],
                    applies_to_month=now.month,
                    applies_to_year=now.year
                )
                insights.append(insight)
        
        # 4. Category trends
        categories = Category.objects.filter(user=user)
        for category in categories:
            trend_data = analyze_category_trends(user, category)
            if abs(trend_data['change']) > 20:  # Significant change
                trend_emoji = '📈' if trend_data['trend'] == 'increasing' else '📉'
                insight = SpendingInsight.objects.create(
                    user=user,
                    insight_type='trend',
                    severity='info',
                    title=f'{trend_emoji} {category.name} spending {trend_data["trend"]}',
                    message=f'Your {category.name} spending has changed by {trend_data["change"]}% compared to 3 months ago.',
                    applies_to_month=now.month,
                    applies_to_year=now.year
                )
                insights.append(insight)
        
        logger.info(f"Generated {len(insights)} insights for user {user.email}")
        return insights
        
    except Exception as e:
        logger.error(f"Insight generation error: {e}", exc_info=True)
        return insights
