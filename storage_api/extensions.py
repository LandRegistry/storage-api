import collections
import json
import logging
import traceback

from flask import ctx, g, request
from flask_logconfig import LogConfig

# Create empty extension objects here
logger = LogConfig()


def register_extensions(app):
    """Adds any previously created extension objects into the app, and does any further setup they need."""
    logger.init_app(app)

    app.audit_logger = logging.getLogger("audit")

    app.logger.info("Extensions registered")


class ContextualFilter(logging.Filter):
    def filter(self, log_record):
        """Provide some extra variables to be placed into the log message"""

        if ctx.has_app_context():
            log_record.trace_id = g.trace_id
            log_record.msg = "Endpoint: {}, Method: {}, Caller: {}.{}[{}], {}".format(
                request.endpoint, request.method, log_record.module, log_record.funcName, log_record.lineno,
                log_record.msg)
        else:
            log_record.trace_id = 'N/A'
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record):
        if record.exc_info:
            exc = traceback.format_exception(*record.exc_info)
        else:
            exc = None

        # Timestamp must be first (webops request)
        log_entry = collections.OrderedDict(
            [('timestamp', self.formatTime(record)),
             ('level', record.levelname),
             ('traceid', record.trace_id),
             ('message', record.msg % record.args),
             ('exception', exc)])

        return json.dumps(log_entry)


class JsonAuditFormatter(logging.Formatter):
    def format(self, record):
        # Timestamp must be first (webops request)
        log_entry = collections.OrderedDict(
            [('timestamp', self.formatTime(record)),
             ('level', 'AUDIT'),
             ('traceid', record.trace_id),
             ('message', record.msg % record.args)])

        return json.dumps(log_entry)
