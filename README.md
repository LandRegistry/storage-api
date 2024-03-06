# Storage API

An API for the storage and retrieval of files such as PDFs and images.

## Documentation

Swagger documentation can be found in storage_api/documentation/storage.yml. This application is built to run on our common development environment (common dev-env), which you can read more about here: https://github.com/LandRegistry/common-dev-env


## Configuration

### STORAGE_TYPE
STORAGE_TYPE indicates the storage solution to be used. `file` should only be used for dev and internal test environments.  This should not be used in production as this will save file to the local disk storage which is not secure.  
 
In production and AWS environments the storage type should be `s3` to save files in the amazon s3 storage solution.
 
Currently this only accepts `file` as an option. As the `s3` adapter has not been built.  Once moving to AWS a s3_storage_adatper should be added and the storage_type_factory updated to accept `s3`.

### FILE_STORAGE_LOCATION 
If `STORAGE_TYPE` is set to `file` then this variable can be used to set which folder the files should be saved in.

## Unit tests

The unit tests are contained in the unit_tests folder. [Pytest](http://docs.pytest.org/en/latest/) is used for unit testing. 

To run the unit tests if you are using the common dev-env use the following command:

```bash
docker-compose exec storage-api make unittest
or, using the alias
unit-test storage-api
```

or

```bash
docker-compose exec storage-api make report="true" unittest
or, using the alias
unit-test storage-api -r
```

## Linting

Linting is performed with [Flake8](http://flake8.pycqa.org/en/latest/). To run linting:
```
docker-compose exec storage-api make lint
```
