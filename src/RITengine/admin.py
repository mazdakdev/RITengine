from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from stats.utils import get_engine_performance, get_engine_performance_over_time
from django.core.serializers.json import DjangoJSONEncoder
import json
from user.utils.general import get_users_stats

class CustomAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('/', self.admin_view(self.statstics_view), name="charts"),
        ]
        return custom_urls + urls

    def statstics_view(self, request):
        engine_performance = get_engine_performance()
        engine_popularity = get_engine_performance_over_time()
        user_stats = get_users_stats()
        print(engine_popularity)

        context = {
            'chart_data': json.dumps(list(engine_performance), cls=DjangoJSONEncoder),
            'popularity_data': json.dumps(list(engine_popularity), cls=DjangoJSONEncoder),
            'registration_data': json.dumps(user_stats['registration_data']),
            'activity_data': json.dumps(user_stats['activity_data']),
            'status_data': json.dumps(user_stats['status_data']),
            'login_frequency_data': json.dumps(user_stats['login_frequency_data']),
        }

        return TemplateResponse(request, "admin/statstics.html", context)


admin_site = CustomAdminSite(name='custom_admin')
