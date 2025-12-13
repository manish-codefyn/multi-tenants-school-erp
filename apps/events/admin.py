from django.contrib import admin
from .models import EventCategory, Event, EventRegistration, EventDocument

@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'color', 'is_active', 'order')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'status', 'priority', 'is_published')
    list_filter = ('event_type', 'status', 'priority', 'is_published', 'academic_year')
    search_fields = ('title', 'description', 'venue')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'start_date'

@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('event', 'get_registrant_name', 'registration_type', 'status', 'registration_date', 'fee_paid')
    list_filter = ('status', 'registration_type', 'fee_paid', 'event')
    search_fields = ('event__title', 'student__first_name', 'student__last_name', 'user__email', 'external_name', 'external_email')
    date_hierarchy = 'registration_date'

    def get_registrant_name(self, obj):
        return obj.get_registrant_name()
    get_registrant_name.short_description = 'Registrant'

@admin.register(EventDocument)
class EventDocumentAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'document_type', 'is_public', 'download_count')
    list_filter = ('document_type', 'is_public', 'event')
    search_fields = ('name', 'event__title')
