from http import HTTPStatus

from django.conf import settings
from django.contrib.messages import get_messages
from django.template.loader import render_to_string


class HtmxMessagesMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response

	def __call__(self, request):
		response = self.get_response(request)
		if (
			request.htmx
			and response.status_code == HTTPStatus.OK
			and response.get("Content-Type") == "text/html"
		):
			messages = get_messages(request)
			if messages:
				rendered_messages = render_to_string(
					settings.HTMX_MESSAGES_MIDDLEWARE_TEMPLATE, {"messages": messages}
				)
				oob_html = f'<div id="{settings.HTMX_MESSAGES_MIDDLEWARE_HTML_ID}" hx-swap-oob="true">{rendered_messages}</div>'
				response.content += oob_html.encode("utf-8")
		return response
