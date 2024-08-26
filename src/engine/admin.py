from django.contrib import admin
from .models import Engine, Message, Chat, EngineCategory, Assist
from django.db.models import Count, Case, When, IntegerField
from stats.models import Vote
from stats.utils import get_engine_performance

@admin.register(Engine)
class EngineAdmin(admin.ModelAdmin):
    change_list_template = "admin/engine_stats.html"

    def changelist_view(self, request, extra_context=None):
        chart_data = get_engine_performance()
        extra_context = extra_context or {}
        extra_context['chart_data'] = list(chart_data)

        return super().changelist_view(request, extra_context=extra_context)

admin.site.register(Message)
admin.site.register(Chat)
admin.site.register(EngineCategory)
admin.site.register(Assist)
