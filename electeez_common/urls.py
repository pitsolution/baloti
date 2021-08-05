from django import http
from django.contrib import admin
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls import url
from django.conf.urls.static import static
from django.views import generic
from django.urls import include, path, reverse
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.templatetags.static import static as static_url


urlpatterns = [
    url(r'^favicon\.ico$', generic.RedirectView.as_view(url='/static/images/favicon.ico')),
]


class HomeView(generic.View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return http.HttpResponseRedirect('/contest/')

        if settings.SITE_ID == 1:
            return http.HttpResponseRedirect(static_url('landing/index.html'))
        else:
            return http.HttpResponseRedirect(reverse('login'))


urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('accounts/', include('electeez_auth.urls')),
    path('contest/', include('djelectionguard.urls')),
    path('tezos/', include('djelectionguard_tezos.views')),
    path('track/', include('djelectionguard_tracker.views')),
    path('', HomeView.as_view()),
)

if settings.DEBUG:
    urlpatterns.append(
        path('bundles/', include('ryzom_django.bundle')),
    )


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += staticfiles_urlpatterns('/static/')
urlpatterns += staticfiles_urlpatterns()


if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
