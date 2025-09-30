
from django.contrib import admin
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('github_application.urls')),

]

# Customizing admin site headers
admin.site.site_header = "GitHub Admin"
admin.site.site_title = "GitHub Admin Portal"
admin.site.index_title = "Welcome to GitHub Admin Portal"

# Custom error handlers
handler404 = 'github_application.views.custom_404'
handler500 = 'github_application.views.custom_500'
handler403 = 'github_application.views.custom_403'
handler400 = 'github_application.views.custom_400'

# Serving media files in development
from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# Note: In production, media files should be served by the web server (e.g., Nginx, Apache)
# and not by Django for better performance and security.
# Also, ensure DEBUG is set to False in production to avoid exposing sensitive information.
