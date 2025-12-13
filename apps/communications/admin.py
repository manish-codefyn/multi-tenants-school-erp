from django.contrib import admin
from .models import (
    CommunicationChannel, CommunicationTemplate, CommunicationCampaign,
    Communication, CommunicationAttachment
)

@admin.register(CommunicationChannel)
class CommunicationChannelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'channel_type', 'is_active', 'is_healthy')
    list_filter = ('channel_type', 'is_active', 'is_healthy')
    search_fields = ('name', 'code')

@admin.register(CommunicationTemplate)
class CommunicationTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'template_type', 'channel', 'language', 'is_active')
    list_filter = ('template_type', 'channel', 'language', 'is_active')
    search_fields = ('name', 'code')

@admin.register(CommunicationCampaign)
class CommunicationCampaignAdmin(admin.ModelAdmin):
    list_display = ('name', 'campaign_type', 'status', 'scheduled_for', 'sent_count')
    list_filter = ('campaign_type', 'status')
    search_fields = ('name',)

@admin.register(Communication)
class CommunicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'channel', 'status', 'priority', 'direction', 'sent_at')
    list_filter = ('status', 'priority', 'direction', 'channel')
    search_fields = ('title', 'subject', 'recipient_id')

@admin.register(CommunicationAttachment)
class CommunicationAttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'communication', 'file_type', 'file_size')
    list_filter = ('file_type',)
    search_fields = ('file_name',)
