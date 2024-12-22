from django.contrib import admin

# Register your models here.
from django.contrib import admin, messages
from django import forms
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Tile, Profile, QueuedAction, ProgressAction, StatusAction, UniversalGoods, GameDate
from .views import resolve_actions

class TileAdminForm(forms.ModelForm):
    """Custom form for Tile admin."""
    class Meta:
        model = Tile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Load universal goods and create fields dynamically
        universal_goods = UniversalGoods.objects.all()
        goods_dict = self.instance.goods if self.instance else {}
        self.goods_fields = []

        for good in universal_goods:
            good_name = good.name
            field_name = f"good_{good_name}"
            initial_value = goods_dict.get(good_name, 0)
            self.fields[field_name] = forms.IntegerField(
                label=f"{good_name.capitalize()} Amount",
                initial=initial_value,
                min_value=0,
                required=False
            )
            self.goods_fields.append(field_name)

    # Hiding the actual JSON goods field
    goods = forms.JSONField(widget=forms.HiddenInput(), required=False)

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Parse the goods JSON data
        goods_data = self.cleaned_data.get('goods', {})

        # If goods_data is None, initialize it as an empty dictionary
        if goods_data is None:
            goods_data = {}

        # If this is a new tile, initialize its goods with all universal goods set to 0
        if instance.pk is None:  # This check ensures we're dealing with a new instance
            # Initialize the goods with universal goods set to 0
            universal_goods = UniversalGoods.objects.all()
            for good in universal_goods:
                goods_data[good.name] = 0

        instance.goods = goods_data  # Store the goods data in the instance

        if commit:
            instance.save()

        # Check if there are any goods that are not part of the UniversalGoods
        for good_name in goods_data.keys():
            if not UniversalGoods.objects.filter(name=good_name).exists():
                UniversalGoods.objects.create(name=good_name)

        # Find goods that have been removed from this tile
        existing_good_names = set(instance.goods.keys())
        all_universal_goods = set(UniversalGoods.objects.values_list('name', flat=True))
        removed_goods = all_universal_goods - existing_good_names
        # Remove from UniversalGoods
        UniversalGoods.objects.filter(name__in=removed_goods).delete()


        return instance

class TileAdmin(admin.ModelAdmin):
    list_display = ('x', 'y', 'owner', 'population', 'buildings', 'resources')  # Display these fields in the admin
    list_filter = ('owner', 'resources')  # Add filters for owner and resources
    search_fields = ('x', 'y', 'owner__username')  # Add search functionality for coordinates and owner
    list_editable = ('owner',)  # Allow inline editing of ownership

    form = TileAdminForm

    class Media:
        js = ('js/admin_tile.js',)

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

    # Custom button to resolve actions
    def resolve_actions_view(self, request):
        resolve_actions(request)  # Call the resolve function
        self.message_user(request, "All actions resolved successfully!", level=messages.SUCCESS)
        return redirect(request.META.get('HTTP_REFERER', 'admin:app_queuedaction_changelist'))

    # Add custom URL for resolve action
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('resolve-actions/', self.admin_site.admin_view(self.resolve_actions_view), name='resolve-actions'),
        ]
        return custom_urls + urls

    # Inject button into the template
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['resolve_actions_url'] = 'resolve-actions/'
        return super().changelist_view(request, extra_context=extra_context)

    # Use a custom template to display the button
    change_list_template = "admin/queued_action_changelist.html"


# Register admin
admin.site.register(QueuedAction, QueuedActionAdmin)


class StatusActionAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'details', 'completion_date', 'user')
    list_filter = ('action_type',)
    search_fields = ('user__username',)


admin.site.register(StatusAction, StatusActionAdmin)


class ProgressActionAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'details', 'turn', 'user')
    list_filter = ('action_type',)
    search_fields = ('user__username',)


admin.site.register(ProgressAction, ProgressActionAdmin)


class GoodsForm(forms.Form):
    """Form for managing goods in tiles."""
    good_name = forms.CharField(max_length=100, required=True)
    good_amount = forms.IntegerField(min_value=0, required=True)

class UniversalGoodsAdmin(admin.ModelAdmin):
    """Admin interface for UniversalGoods."""
    list_display = ('name',)


admin.site.register(UniversalGoods, UniversalGoodsAdmin)


class GameDateAdmin(admin.ModelAdmin):
    list_display = ('current_date',)
    fields = ('current_date',)


admin.site.register(GameDate, GameDateAdmin)
