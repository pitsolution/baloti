from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views import generic
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('contest/', include('djelectionguard.views')),
    path('', generic.RedirectView.as_view(url='/contest/')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
