"""
class HtmxActionView(HtmxActionMixin, View):
	success_url = "/success"
	failure_url = "/fail".

	def perform_action(self):
		if self.kwargs.get("error"):
			self.add_message(str(self.kwargs["error"]), messages.ERROR)
		return
@patch("django.contrib.messages.add_message")
class HtmxActionMixinTests(TestCase):
	factory = RequestFactory()

	@parameterized.expand(
		[(error, htmx) for error in (True, False) for htmx in (True, False)],
		name_func=lambda func, param_num, param: f"{func.__name__}_"
		+ ("has_error" if param.args[0] else "no_error")
		+ "_"
		+ ("with_htmx" if param.args[1] else "without_htmx"),
	)
	def test_htmx_action(self, mock_add_message, error, htmx):
		request = self.factory.post(
			"/", headers={"HX-Request": "true" if htmx else "false"}
		)
		request.htmx = HtmxDetails(request)
		response = HtmxActionView.as_view()(request, error=error)
		if error:
			if htmx:
				self.assertTrue(bool(request.htmx))
				self.assertIn(
					"components/messages.html",
					response.template_name,
				)
			else:
				self.assertFalse(bool(request.htmx))
				self.assertEqual(response.url, HtmxActionView.failure_url)
			mock_add_message.assert_called()
		else:
			self.assertEqual(response.url, HtmxActionView.success_url)
"""
