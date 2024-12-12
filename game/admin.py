from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from .models import Tile, Profile, QueuedAction
from .views import resolve_actions

class TileAdmin(admin.ModelAdmin):
    list_display = ('x', 'y', 'owner', 'buildings', 'resources')  # Display these fields in the admin
    list_filter = ('owner', 'resources')  # Add filters for owner and resources
    search_fields = ('x', 'y', 'owner__username')  # Add search functionality for coordinates and owner
    list_editable = ('owner',)  # Allow inline editing of ownership

admin.site.register(Tile, TileAdmin)


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'color', 'money')  # Show user and money in the list view
    list_editable = ('display_name', 'color', 'money',)  # Allow inline editing of money
    search_fields = ('user__username',)  # Search by username

admin.site.register(Profile, UserProfileAdmin)


class QueuedActionAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'details', 'timestamp', 'user')
    list_filter = ('action_type',)
    search_fields = ('user__username',)

    # Add a custom button for resolving actions
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('resolve-actions/', self.admin_site.admin_view(self.resolve_actions_view), name='resolve-actions'),
        ]
        return custom_urls + urls

    def resolve_actions_view(self, request):
        # Redirect to the resolve actions view
        resolve_actions(request)
        self.message_user(request, "Actions resolved successfully!")
        return redirect("..")


admin.site.register(QueuedAction, QueuedActionAdmin)