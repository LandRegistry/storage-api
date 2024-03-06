from storage_api.views import general
from storage_api.views.v1_0 import storage as storage_v1_0


def register_blueprints(app):
    """Adds all blueprint objects into the app."""
    app.register_blueprint(general.general)
    app.register_blueprint(storage_v1_0.storage_bp, url_prefix='/v1.0/storage')

    app.logger.info("Blueprints registered")
