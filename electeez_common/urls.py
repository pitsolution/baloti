from django import http
from django.contrib import admin, messages
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls import url
from django.conf.urls.static import static
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
from django.urls import include, path, reverse
from django.utils.decorators import method_decorator
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.templatetags.static import static as static_url
from django.contrib.auth import views as auth_views

from djlang.utils import gettext as _


urlpatterns = [
    url(r'^favicon\.ico$', generic.RedirectView.as_view(url='/static/images/favicon.ico')),
]


@method_decorator(csrf_exempt, name='dispatch')
class HomeView(generic.TemplateView):
    def dispatch(self, request, *args, **kwargs):
        url = reverse('login')

        if request.user.is_authenticated:
            url = reverse('contest_list')

        elif home_page := getattr(settings, 'STATIC_HOME_PAGE', None):
            url = static_url(home_page)

        elif template := getattr(settings, 'HOME_TEMPLATE', None):
            self.template_name = template
            return super().dispatch(request, *args, **kwargs)

        return http.HttpResponseRedirect(url)

    def post(self, request, *args, **kwargs):
        if 'inputEmail' in request.POST:
            messages.success(
                request,
                _('You have successfully subscribed to %(app)s mailing list',
                    app=_('Neuilly Vote')
                )
            )
        return self.get(request, *args, **kwargs)


urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('accounts/', include('electeez_auth.urls')),
    path('contest/', include('djelectionguard.urls')),
    path('tezos/', include('djelectionguard_tezos.views')),
    path('track/', include('djelectionguard_tracker.views')),
    path('lang/', include('djlang.views')),
    path('', HomeView.as_view(), name='home'),
    path('baloti/', include(('baloti_auth.urls', 'baloti'), namespace="baloti"), name='baloti'),
    path('baloti/', include(('baloti_djelectionguard.urls', 'baloti_djelectionguard'), namespace="baloti_djelectionguard"), name='baloti_djelectionguard'),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path('social-auth/', include('social_django.urls', namespace="social")),
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
