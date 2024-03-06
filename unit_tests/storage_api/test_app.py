from unittest import TestCase
from unittest.mock import Mock, patch

from flask import g
from jwt_validation.exceptions import ValidationFailure
from storage_api import app, main
from storage_api.exceptions import ApplicationError


class TestApp(TestCase):

    TRACE_ID = 'some trace id'
    X_API_Version = '1.0.0'

    @patch('storage_api.app.validate')
    @patch('storage_api.app.uuid')
    @patch('storage_api.app.RequestsSessionTimeout')
    def test_before_request(self, requests_mock, uuid_mock, validate):
        # Should set a uuid trace id, update the trace id on global, assign the session to the global object,
        # check and set auth header.
        with main.app.app_context():
            with main.app.test_request_context(headers={
                "X-Trace-ID": self.TRACE_ID,
                "Authorization": "Fake JWT"
            }, method="POST"):
                session_mock = Mock()
                requests_mock.return_value = session_mock

                app.before_request()

                self.assertEqual(g.trace_id, self.TRACE_ID)
                self.assertEqual(g.requests, session_mock)

                g.requests.headers.update.assert_any_call({'X-Trace-ID': self.TRACE_ID})
                g.requests.headers.update.assert_any_call({'Authorization': "Fake JWT"})

    @patch('storage_api.app.validate')
    @patch('storage_api.app.uuid')
    @patch('storage_api.app.RequestsSessionTimeout')
    def test_before_request_unauth(self, requests_mock, uuid_mock, validate):
        # Should set a uuid trace id, update the trace id on global, assign the session to the global object,
        # fail check of auth header and throw an exception
        with main.app.app_context():
            with main.app.test_request_context(headers={
                "X-Trace-ID": self.TRACE_ID,
                "Authorization": "Fake JWT"
            }, method="POST"):
                session_mock = Mock()
                requests_mock.return_value = session_mock

                validate.side_effect = ValidationFailure("Invalid")

                with self.assertRaises(ApplicationError):
                    app.before_request()

                self.assertEqual(g.trace_id, self.TRACE_ID)
                self.assertEqual(g.requests, session_mock)

                g.requests.headers.update.assert_any_call({'X-Trace-ID': self.TRACE_ID})

    @patch('storage_api.app.validate')
    @patch('storage_api.app.uuid')
    @patch('storage_api.app.RequestsSessionTimeout')
    def test_before_request_noauth(self, requests_mock, uuid_mock, validate):
        # Should set a uuid trace id, update the trace id on global, assign the session to the global object,
        # fail to find auth header and throw an exception
        with main.app.app_context():
            with main.app.test_request_context(headers={
                "X-Trace-ID": self.TRACE_ID
            }, method="POST"):
                session_mock = Mock()
                requests_mock.return_value = session_mock

                with self.assertRaises(ApplicationError):
                    app.before_request()

                self.assertEqual(g.trace_id, self.TRACE_ID)
                self.assertEqual(g.requests, session_mock)

                g.requests.headers.update.assert_any_call({'X-Trace-ID': self.TRACE_ID})

    @patch('storage_api.app.validate')
    @patch('storage_api.app.uuid')
    @patch('storage_api.app.RequestsSessionTimeout')
    def test_before_request_noauth_get(self, requests_mock, uuid_mock, validate):
        # Should set a uuid trace id, update the trace id on global, and assign the session to the global object.
        with main.app.app_context():
            with main.app.test_request_context(headers={
                "X-Trace-ID": self.TRACE_ID,
                "Authorization": "Fake JWT"
            }, method="GET"):
                session_mock = Mock()
                requests_mock.return_value = session_mock

                app.before_request()

                self.assertEqual(g.trace_id, self.TRACE_ID)
                self.assertEqual(g.requests, session_mock)

                g.requests.headers.update.assert_any_call({'X-Trace-ID': self.TRACE_ID})

    def test_after_request(self):
        # Should set the X-API-Version to the expected value.
        response_mock = Mock()
        response_mock.headers = {
            "X-API-Version": None
        }
        result = app.after_request(response_mock)

        self.assertEqual(result.headers["X-API-Version"], self.X_API_Version)
