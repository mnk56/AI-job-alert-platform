from django.contrib import admin
from .models import Company, InterviewSession, ChatLog, Tag


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ('name',)
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at')
    search_fields = ('name', 'description')
    filter_horizontal = ('tags',)
    raw_id_fields = ('owner',)
@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ('company', 'challenger', 'status', 'score', 'created_at', 'finished_at')
    list_filter = ('status', 'company')
    search_fields = ('company__name', 'challenger__username')
    autocomplete_fields = ('company', 'challenger')   
@admin.register(ChatLog)
class ChatLogAdmin(admin.ModelAdmin):
    list_display = ('session', 'role', 'created_at')
    list_filter = ('role', 'session__company')
    search_fields = ('message', 'session__company__name')