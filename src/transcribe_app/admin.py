from django.contrib import admin
from django.utils.html import format_html
from django.conf import settings

from .models import Transcript


@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ('short_id', 'filename', 'status', 'created_at', 'download_link')
    list_filter = ('status', 'created_at')
    search_fields = ('filename', 'transcript')
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
    actions = ('mark_done', 'mark_processing', 'mark_error')

    def short_id(self, obj):
        return str(obj.id)[:8]
    short_id.short_description = 'ID'

    def download_link(self, obj):
        if not obj.filename:
            return '-'
        media_url = settings.MEDIA_URL if settings.MEDIA_URL.endswith('/') else settings.MEDIA_URL + '/'
        url = f"{media_url}{obj.filename}"
        return format_html('<a href="{}" target="_blank" rel="noopener">Download</a>', url)
    download_link.short_description = 'Audio'

    def mark_done(self, request, queryset):
        queryset.update(status='done')
    mark_done.short_description = 'Mark selected as done'

    def mark_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_processing.short_description = 'Mark selected as processing'

    def mark_error(self, request, queryset):
        queryset.update(status='error')
    mark_error.short_description = 'Mark selected as error'
