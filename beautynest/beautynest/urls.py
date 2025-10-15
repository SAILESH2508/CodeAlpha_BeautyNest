from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin  # ✅ Correct import
from django.urls import include, path
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', include('shop.urls')),  # main shop app
    path('admin/', admin.site.urls),  # Django admin
    path('accounts/', include('django.contrib.auth.urls')),
    path("login/", auth_views.LoginView.as_view(), name="login"),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
