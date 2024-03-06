import json

import pyclamd
from flask import Blueprint, Response, current_app, request, send_file
from storage_api.config import CLAMD_HOST, CLAMD_PORT
from storage_api.dependencies import storage_type_factory
from storage_api.exceptions import ApplicationError
from storage_api.model.storage_item import StorageItem

storage_bp = Blueprint('storage', __name__)


@storage_bp.route('/<bucket>/<file_id>', methods=['GET'])
def get_file(bucket, file_id):
    """Get a file with the provided file_id from the provided bucket"""
    current_app.logger.info("Retrieve Endpoint called")
    subdirectories = request.args.get('subdirectories')
    storage_location = storage_type_factory.get_storage_type()
    send_as_attachment = False
    try:
        if storage_location.is_directory(bucket, file_id, subdirectories):
            archive_name = request.args.get('archive_name')
            stored_item = storage_location.zip_directory(bucket, file_id, subdirectories, archive_name)
            send_as_attachment = True
        else:
            stored_item = storage_location.get_file(bucket, file_id, subdirectories)
    except Exception as ex:
        error_message = 'Failed to retrieve the requested file. Exception - {}'\
            .format(ex)
        current_app.logger.exception(error_message)
        raise ApplicationError(error_message, 'G01')
    if stored_item and stored_item.file:
        current_app.logger.info("File returned  building response")
        if send_as_attachment:
            return send_file(stored_item.file, mimetype=stored_item.meta_type, as_attachment=True,
                             download_name=stored_item.file_name), 200
        else:
            return send_file(stored_item.file, mimetype=stored_item.meta_type), 200
    else:
        raise ApplicationError("File not found", 404, 404)


@storage_bp.route('/<bucket>/<file_id>/external-url', methods=['GET'])
def get_file_external_url(bucket, file_id):
    """Get external URL of a file provided file_id from the provided bucket"""
    current_app.logger.info("Retrieve Endpoint called")
    subdirectories = request.args.get('subdirectories')
    storage_location = storage_type_factory.get_storage_type()
    try:
        result = storage_location.get_file_external_url(bucket, file_id, subdirectories)
        if result is None:
            raise ApplicationError("File not found", 404, 404)
        response = Response()
        response.status_code = 200
        response.content_type = 'application/json'
        response.data = json.dumps(result)
        return response
    except ApplicationError:
        raise
    except Exception as ex:
        error_message = 'Failed to retrieve external url requested file. Exception - {}' \
            .format(ex)
        current_app.logger.exception(error_message)
        raise ApplicationError(error_message, 'G01')


@storage_bp.route('/<bucket>/<file_id>', methods=['DELETE'])
def delete_file(bucket, file_id):
    """Delete a file with the provided file_id from the provided bucket"""
    current_app.logger.info("Delete Endpoint called")
    try:
        storage_location = storage_type_factory.get_storage_type()
        if storage_location.delete_file(bucket, file_id):
            return '', 204
        else:
            raise ApplicationError("File not found", 404, 404)
    except ApplicationError:
        raise
    except Exception as ex:
        error_message = 'Failed to delete the requested file. Exception - {}' \
            .format(ex)
        current_app.logger.exception(error_message)
        raise ApplicationError(error_message, 'D01')


@storage_bp.route('/<bucket>', methods=['POST'])
def save_file(bucket):
    """Save a file to the provided bucket"""
    current_app.logger.info("Save Endpoint called")

    if len(request.files) > 0:
        result = {}
        subdirectories = request.args.get('subdirectories')
        scan = request.args.get('scan')

        for file_key in request.files:
            file = request.files[file_key]

            if scan == 'True':
                # Scan the file for threats
                if CLAMD_HOST and CLAMD_PORT:
                    clamd = pyclamd.ClamdNetworkSocket(host=CLAMD_HOST, port=CLAMD_PORT)
                else:
                    clamd = pyclamd.ClamdUnixSocket()
                threat_found = clamd.scan_stream(file.read())
                file.seek(0)

                if threat_found:
                    rollback(result)
                    raise ApplicationError("Virus scan failed on uploaded document", 400, 400)
            try:
                if result.get(file_key) is None:
                    result[file_key] = []
                item = StorageItem(file, file.content_type, file.filename)
                storage_location = storage_type_factory.get_storage_type()
                saved_item = storage_location.save_file(bucket, item, subdirectories)
                result.get(file_key).append(saved_item)
            except Exception as ex:
                error_message = 'Failed to save the requested file. Exception  {}' \
                    .format(ex)
                current_app.logger.exception(error_message)
                rollback(result)
                raise ApplicationError('Failed to save the requested file. Rolling back any changes', 'S-01')

        response = Response()
        response.status_code = 201
        response.content_type = 'application/json'
        response.data = json.dumps(result)
        return response
    else:
        raise ApplicationError("No File in request", 400, 400)


def rollback(files):
    try:
        storage_location = storage_type_factory.get_storage_type()
        for file_key in files:
            for saved_item in files[file_key]:
                storage_location.delete_file(saved_item['bucket'], saved_item['file_id'],
                                             saved_item.get('subdirectories'))
    except Exception as ex:
        error_message = 'Failed to rollback. Exception - {}' \
            .format(ex)
        current_app.logger.exception(error_message)
