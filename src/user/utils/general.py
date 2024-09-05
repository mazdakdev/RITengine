from django.db.models import Count, F
from django.db.models.functions import ExtractMonth, ExtractYear
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Q
from typing import Optional
from django.contrib.auth import get_user_model

User = get_user_model()


def get_user_by_identifier(identifier: str, case_sensitive: bool = True) -> Optional[User]:
    """
    Fetch a user by either username, email, or phone number.
    """
    lookup_args = {
        'username__iexact': identifier,
        'email__iexact': identifier,
        'phone_number__iexact': identifier
    }

    if case_sensitive:
        lookup_args = {
            'username': identifier,
            'email': identifier,
            'phone_number': identifier
        }

    filters = Q()
    for field, value in lookup_args.items():
        filters |= Q(**{field: value})  # Combine using bitwise OR

    try:
        user = User.objects.get(filters)
        return user
    except User.DoesNotExist:
        return None
    except User.MultipleObjectsReturned:
        return None

def get_users_stats():
    """
    Retrieve and annotate all users statistics for various charts.
    """

    # User Registration Trends
    registrations_by_month = User.objects.annotate(
        year=ExtractYear('created_at'),
        month=ExtractMonth('created_at')
    ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')

    registration_data = {
        'labels': [f"{entry['month']}/{entry['year']}" for entry in registrations_by_month],
        'datasets': [{
            'label': 'User Registrations',
            'data': [entry['count'] for entry in registrations_by_month],
            'backgroundColor': 'rgba(75, 192, 192, 0.2)',
            'borderColor': 'rgba(75, 192, 192, 1)',
            'borderWidth': 1,
        }]
    }

    # User Activity
    start_date = now() - timedelta(days=30)
    activity_by_day = User.objects.filter(last_login__gte=start_date).annotate(
        date=F('last_login__date')
    ).values('date').annotate(count=Count('id')).order_by('date')

    activity_data = {
        'labels': [entry['date'].strftime('%Y-%m-%d') for entry in activity_by_day],
        'datasets': [{
            'label': 'User Activity',
            'data': [entry['count'] for entry in activity_by_day],
            'backgroundColor': 'rgba(153, 102, 255, 0.2)',
            'borderColor': 'rgba(153, 102, 255, 1)',
            'borderWidth': 1,
        }]
    }

    # User Status
    user_status = User.objects.values('is_active').annotate(count=Count('id'))

    status_data = {
        'labels': ['Active', 'Inactive'],
        'datasets': [{
            'label': 'User Status',
            'data': [entry['count'] for entry in user_status],
            'backgroundColor': ['rgba(75, 192, 192, 0.2)', 'rgba(255, 99, 132, 0.2)'],
            'borderColor': ['rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)'],
            'borderWidth': 1,
        }]
    }

    # User Login Frequency
    login_frequency_by_month = User.objects.filter(last_login__gte=start_date).annotate(
        year=ExtractYear('last_login'),
        month=ExtractMonth('last_login')
    ).values('year', 'month').annotate(count=Count('id')).order_by('year', 'month')

    login_frequency_data = {
        'labels': [f"{entry['month']}/{entry['year']}" for entry in login_frequency_by_month],
        'datasets': [{
            'label': 'User Login Frequency',
            'data': [entry['count'] for entry in login_frequency_by_month],
            'backgroundColor': 'rgba(255, 159, 64, 0.2)',
            'borderColor': 'rgba(255, 159, 64, 1)',
            'borderWidth': 1,
        }]
    }

    # Combine all data
    return {
        'registration_data': registration_data,
        'activity_data': activity_data,
        'status_data': status_data,
        'login_frequency_data': login_frequency_data,
    }
