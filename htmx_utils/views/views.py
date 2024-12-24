from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin

from .mixins import HtmxActionMixin


class HtmxActionView(HtmxActionMixin, View):
	"""
	A class representing a view with HTMX action capabilities.

	This class inherits from the HtmxActionMixin and View classes.

	Class Attributes:
	    None

	Instance Attributes:
	    None

	Methods:
	    None
	"""

	pass


class HtmxModelActionView(SingleObjectMixin, HtmxActionView):
	def post(self, request, *args, **kwargs):
		self.object = self.get_object()
		return super().post(request, *args, **kwargs)
