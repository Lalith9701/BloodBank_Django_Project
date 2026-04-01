from django.contrib import admin
from .models import Rating

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('blood_request', 'rater', 'donor_rating', 'service_rating', 'created_at')
    list_filter = ('donor_rating', 'service_rating')
    search_fields = ('blood_request__user__username', 'rater__username', 'feedback')
