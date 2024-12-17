from django.http import HttpRequest


class Action:
	def __init__(self, request: HttpRequest = None, **kwargs):
		self.result = None
		self.request = request
		self._errors = []
		self._messages = []
		self.action_performed = False
		self.action_kwargs = kwargs or {}

	@property
	def errors(self) -> list:
		if not self.action_performed:
			self.perform_action()
		return self._errors

	@property
	def messages(self) -> list:
		return self._messages

	def is_valid(self) -> bool:
		return self.action_performed and not self.errors

	def perform_action(self):
		self.result = self.action(**self.action_kwargs)
		self.action_performed = True
		return self.result

	def action(self, **kwargs):
		raise NotImplementedError("You must implement an action to perform")

	def add_error(self, error):
		self._errors.append(error)

	def add_message(self, message, level=None):
		self._messages.append((message, level))
