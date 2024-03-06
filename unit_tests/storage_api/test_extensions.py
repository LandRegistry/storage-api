import collections
import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

from flask import g
from storage_api.extensions import (ContextualFilter, JsonAuditFormatter,
                                    JsonFormatter, register_extensions)
from storage_api.main import app


class TestExtensions(TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.contextual_filter = ContextualFilter()
        self.json_formatter = JsonFormatter()
        self.json_audit_formatter = JsonAuditFormatter()

    @patch('storage_api.extensions.logging')
    @patch('storage_api.extensions.logger')
    def test_register_extensions(self, mock_logger, mock_logging):
        test_app = MagicMock()
        register_extensions(test_app)

        mock_logger.init_app.assert_called_with(test_app)
        mock_logging.getLogger.assert_called_with("audit")
        test_app.logger.info.assert_called_with("Extensions registered")

    def test_contextual_filter_sets_trace_id(self):
        with app.test_request_context():
            g.trace_id = "123"
            test_record = MagicMock()
            self.contextual_filter.filter(test_record)

            self.assertEqual(g.trace_id, test_record.trace_id)

    def test_contextual_filter_doesnt_set_trace_id(self):
        test_record = MagicMock()
        self.contextual_filter.filter(test_record)

        self.assertEqual(test_record.trace_id, 'N/A')

    def test_json_formatter(self):
        test_record = MagicMock()
        test_record.trace_id = '123'
        test_record.msg = 'test'
        test_record.levelname = 'INFO'
        test_record.exc_info = None

        expected_log_entry = collections.OrderedDict(
            [
                ('level', 'INFO'),
                ('traceid', '123'),
                ('message', 'test'),
                ('exception', None)
            ]
        )

        returned_log_entry = self.json_formatter.format(test_record)
        # Convert to JSON string and remove braces
        expected_log_entry_string = json.dumps(expected_log_entry)[1:-1]

        # Check expected items are contained in log entry
        self.assertNotEqual(returned_log_entry.find(expected_log_entry_string), -1)

    @patch('storage_api.extensions.traceback')
    def test_json_formatter_exception(self, traceback_mock):
        test_record = MagicMock()
        test_record.trace_id = '123'
        test_record.msg = 'test'
        test_record.levelname = 'INFO'
        test_record.exc_info = 'test'

        traceback_mock.format_exception.return_value = 'test_exception'

        expected_log_entry = collections.OrderedDict(
            [
                ('level', 'INFO'),
                ('traceid', '123'),
                ('message', 'test'),
                ('exception', 'test_exception')
            ]
        )

        returned_log_entry = self.json_formatter.format(test_record)
        # Convert to JSON string and remove braces
        expected_log_entry_string = json.dumps(expected_log_entry)[1:-1]

        # Check expected items are contained in log entry
        self.assertNotEqual(returned_log_entry.find(expected_log_entry_string), -1)

    def test_json_audit_formatter(self):
        test_record = MagicMock()
        test_record.trace_id = '123'
        test_record.msg = 'test'

        expected_log_entry = collections.OrderedDict(
            [
                ('level', 'AUDIT'),
                ('traceid', '123'),
                ('message', 'test')
            ]
        )

        returned_log_entry = self.json_audit_formatter.format(test_record)
        # Convert to JSON string and remove braces
        expected_log_entry_string = json.dumps(expected_log_entry)[1:-1]

        # Check expected items are contained in log entry
        self.assertNotEqual(returned_log_entry.find(expected_log_entry_string), -1)
