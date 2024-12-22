"""
URL configuration for wargame project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path
from django.contrib.auth import views as auth_views
from game.views import map_view, queue_action, resolve_actions, check_ownership, get_user_actions, remove_action, calculate_path, get_user_data

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', auth_views.LoginView.as_view(template_name='index.html'), name='index'),  # Root URL points to login
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('map/', map_view, name='map'),  # Map view
    path('queue_action/', queue_action, name='queue_action'),
    path('resolve_actions/', resolve_actions, name='resolve_actions'),
    path('check_ownership/', check_ownership, name='check_ownership'),
    path('get_user_actions/', get_user_actions, name='get_user_actions'),
    path('remove_action/<int:action_id>/', remove_action, name='remove_action'),
    path('calculate_path/', calculate_path, name='calculate_path'),
    path('get_user_data/', get_user_data, name='get_user_data'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
