from django.conf import settings
from django.contrib import admin
from django.conf.urls import url, include
from django.urls import path
from overview.views import index


urlpatterns = [
    url(r'^$',index,name='index'),
    url(r'^admin/', admin.site.urls),
    url(r'^index',index),
    url(r'^overview/', include('overview.urls')),
    url(r'^monitor/', include('monitor.urls')),
    url(r'^lookglass/', include('lookglass.urls')),
    #path('accounts/', include('django.contrib.auth.urls')),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    # Serve static and media files from development server
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'MonitorPortal'
