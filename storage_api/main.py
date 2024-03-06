from storage_api.app import app
from storage_api.blueprints import register_blueprints
from storage_api.exceptions import register_exception_handlers
from storage_api.extensions import register_extensions

register_extensions(app)
register_exception_handlers(app)
register_blueprints(app)
