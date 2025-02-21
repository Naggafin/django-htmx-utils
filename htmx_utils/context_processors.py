from django.conf import settings


def htmx_utils_context(request):
	return {
		"HTMX_MESSAGES_MIDDLEWARE_HTML_ID": settings.HTMX_MESSAGES_MIDDLEWARE_HTML_ID,
	}
