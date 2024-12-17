import logging

from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ImproperlyConfigured
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import FormMixin
from django_htmx.http import HttpResponseClientRedirect

from ..actions import Action

logger = logging.getLogger(__name__)


class HtmxFormMixin(FormMixin):
	"""
	A mixin class for handling HTML forms in an htmx-enabled view.

	This mixin extends the functionality of the FormMixin class by adding support for htmx requests. It provides the methods `form_valid` and `form_invalid` which are called when the form is submitted and validated or invalidated, respectively.

	The `form_valid` method checks if the request is an htmx request and if the response is a redirection. If both conditions are met, it returns an `HttpResponseClientRedirect` with the new URL. Otherwise, it returns the original response.

	The `form_invalid` method checks if the request is an htmx request. If it is, it returns an `HttpResponse` with the string representation of the form. Otherwise, it calls the `form_invalid` method of the parent class.

	This mixin is intended to be used in conjunction with htmx-enabled views to provide seamless form handling with dynamic updates.
	"""

	def form_valid(self, form):
		"""
		Ensure the form is valid and return an appropriate response.

		:param form: The form instance that was submitted.
		:type form: django.forms.Form

		:return: The response after processing the form.
		:rtype: django.http.HttpResponseBase

		:raise HttpResponseClientRedirect: If the request is an HTMX request and the response is a redirect.

		Note: This method is called by the Django framework during form validation and processing.
		"""
		response = super().form_valid(form)
		if self.request.htmx and isinstance(response, HttpResponseRedirect):
			return HttpResponseClientRedirect(response.url)
		return response

	def form_invalid(self, form):
		"""
		Handle invalid form submission.

		:param form: The invalid form object.
		:type form: django.forms.Form

		:return: If the request is an htmx request, return an HttpResponse containing the string representation of the form. Otherwise, call the parent's form_invalid() method.
		:rtype: django.http.HttpResponse or django.views.generic.edit.FormMixin
		"""
		if self.request.htmx:
			return HttpResponse(str(form))
		return super().form_invalid(form)


class HtmxActionMixin(AccessMixin, TemplateResponseMixin, ContextMixin):
	"""
	A mixin class that provides common functionality for handling actions in HTMX views.

	Extends:
	    - `AccessMixin`: mixin class that provides access restriction functionality.
	    - `TemplateResponseMixin`: mixin class that provides template rendering functionality.
	    - `ContextMixin`: mixin class that provides context data functionality.

	Properties:
	    - `action_class`: The class representing the action to be performed.
	    - `action_kwargs`: The keyword arguments for the action class.
	    - `success_url`: The URL to redirect to after a successful action.
	    - `failure_url`: The URL to redirect to after an unsuccessful action.

	Methods:
	    - `post()`: Handles the HTTP POST request and performs the specified action.
	    - `put()`: Handles the HTTP PUT request by calling the `post()` method.
	    - `get_action_class()`: Returns the class representing the action.
	    - `get_action_kwargs()`: Returns the keyword arguments for the action.
	    - `get_action()`: Creates an instance of the action class with the specified arguments.
	    - `action_valid()`: Handles the response when the action is valid.
	    - `action_invalid()`: Handles the response when the action is invalid.
	    - `get_success_url()`: Returns the success URL.
	    - `get_failure_url()`: Returns the failure URL.
	    - `get_template_names()`: Returns the template names based on the action data.
	    - `handle_no_permission()`: Handles the response when the user has no permission.

	Raises:
	    - `ImproperlyConfigured`: If no success_url or failure_url is provided.
	"""

	action_class: Action = None
	action_kwargs: dict = None
	success_url: str = None
	failure_url: str = None

	def post(self, request, *args, **kwargs):
		"""
		Handle a POST request and execute an action.

		:param request: The HTTP request object.
		:type request: HttpRequest
		:param args: Additional positional arguments.
		:param kwargs: Additional keyword arguments.

		:return: The result of the action or an HTTP response.
		:rtype: any

		:raise: None
		"""
		action = self.get_action()
		result = action.perform_action()
		if isinstance(result, HttpResponse):
			return result
		if action.is_valid():
			return self.action_valid(action)
		else:
			return self.action_invalid(action)

	def put(self, request, *args, **kwargs):
		"""
		Perform a POST request.

		:param request: The HTTP request object.
		:type request: HttpRequest

		:param args: Positional arguments.
		:type args: tuple

		:param kwargs: Keyword arguments.
		:type kwargs: dict

		:return: The response of the POST request.
		:rtype: HttpResponse
		"""
		return self.post(request, *args, **kwargs)

	def get_action_class(self):
		"""
		Get the action class.

		:return: The action class.
		:rtype: class
		"""
		return self.action_class

	def get_action_kwargs(self):
		"""
		Get the keyword arguments for an action.

		:return: A dictionary containing the keyword arguments.
		:rtype: dict
		"""
		kwargs = {"request": self.request}
		if self.action_kwargs:
			kwargs.update(self.action_kwargs)
		return kwargs

	def get_action(self, action_class: type[Action] = None):
		"""
		Get an instance of an action class.

		:param action_class: (Optional) A class object of the action. If not provided, the default action class will be used.
		:type action_class: type[Action]

		:return: An instance of the action class.
		:rtype: object

		:raise: None

		Note:
		- If the `action_class` parameter is not provided, the function will retrieve the default action class using `self.get_action_class()`.
		- The function will then create an instance of the action class with the keyword arguments obtained from `self.get_action_kwargs()`.
		"""
		action_class = action_class or self.get_action_class()
		return action_class(**self.get_action_kwargs())

	def action_valid(self, action: Action = None):
		"""
		Check if an action is valid and perform the necessary operations.

		:param action: An instance of the Action class.
		:type action: Action, optional

		:return: The response generated by the action.
		:rtype: HttpResponse

		:raise ImproperlyConfigured: If there is an error in the configuration.
		"""
		# make a template response for htmx if configured to
		if self.request.htmx:
			try:
				context = self.get_context_data(action=action)
				return self.render_to_response(context)
			except ImproperlyConfigured as e:
				logger.warning(e)
		# otherwise, default to using the messages system and redirecting
		for message, level in action.messages:
			messages.add_message(self.request, level or messages.INFO, message)
		response = redirect(self.get_success_url())
		if self.request.htmx:
			response = HttpResponseClientRedirect(response.url)
		return response

	def action_invalid(self, action: Action = None):
		"""
		Perform an invalid action and handle the response.

		:param action: An optional Action object representing the action that resulted in an error.
		:type action: Action, optional

		:return: The response generated after handling the invalid action.
		:rtype: HttpResponse or HttpResponseClientRedirect

		:raises ImproperlyConfigured: If there is an issue with the configuration.
		"""
		# make a template response for htmx if configured to
		if self.request.htmx:
			try:
				context = self.get_context_data(action=action)
				return self.render_to_response(context)
			except ImproperlyConfigured as e:
				logger.warning(e)
		# otherwise, default to using the messages system and redirecting
		for error in action.errors:
			messages.error(self.request, error)
		response = redirect(self.get_failure_url())
		if self.request.htmx:
			response = HttpResponseClientRedirect(response.url)
		return response

	def get_success_url(self):
		"""
		Get the success URL for redirecting.

		:return: The success URL.
		:rtype: str

		:raise ImproperlyConfigured: If no success URL is provided.
		"""
		if not self.success_url:
			raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
		return str(self.success_url)

	def get_failure_url(self):
		"""
		Get the URL to redirect to in case of failure.

		:return: The failure URL.
		:rtype: str

		:raise ImproperlyConfigured: If the failure URL is not provided.
		"""
		if not self.failure_url:
			raise ImproperlyConfigured("No URL to redirect to. Provide a failure_url.")
		return str(self.failure_url)

	def get_template_names(self, action: Action = None):
		"""
		Like the regular 'get_template_names' method, except with
		the ability to determine the correct template based upon
		any particular action data.
		"""
		return super().get_template_names()

	def handle_no_permission(self):
		"""
		Handle the case when the user does not have permission to access a resource.

		:return: The response for the user when they do not have permission.
		:rtype: HttpResponse

		:raise: None
		"""
		response = super().handle_no_permission()
		if self.request.htmx:
			return HttpResponseClientRedirect(response.url)
		return response
