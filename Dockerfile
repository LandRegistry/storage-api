# Set the base image to the s2i image
FROM docker-registry/stp/stp-s2i-python-extended:3.9

ENV APP_NAME storage-api

# Development environment values
# These values are not the same as our production environment
# Location the API will use for storage, either file or S3
ENV STORAGE_TYPE="file" \
    LOG_LEVEL="DEBUG" \
    FILE_STORAGE_LOCATION="storage-items" \
    FILE_EXTERNAL_URL_BASE="http://localhost:9008/v1.0/storage" \
    MAX_HEALTH_CASCADE=6 \
    AUTHENTICATION_API_URL="http://dev-search-authentication-api:8080/v2.0" \
    AUTHENTICATION_API_ROOT="http://dev-search-authentication-api:8080" \
    S3_BUCKET="local-land-charges" \
    S3_URL_EXPIRE_IN_SECONDS=43200 \
    APP_MODULE='storage_api.main:app' \
    GUNICORN_ARGS='--reload' \
    WEB_CONCURRENCY='2' \
    DEFAULT_TIMEOUT="30" \
    PYTHONPATH=/src

# Switch from s2i's non-root user back to root for the following commmands
USER root

# Create a user that matches dev-env runner's host user
# And ensure they have access to the jar folder at runtime
ARG OUTSIDE_UID
ARG OUTSIDE_GID
RUN groupadd --force --gid $OUTSIDE_GID containergroup && \
    useradd --uid $OUTSIDE_UID --gid $OUTSIDE_GID containeruser

ADD requirements_test.txt requirements_test.txt
ADD requirements.txt requirements.txt
RUN pip3 install -r requirements.txt && \
    pip3 install -r requirements_test.txt

RUN yum install -y clamd && yum clean all -y -q && ln -sf /etc/clamd.d/scan.conf /etc/clamd.conf && \
    rm -rf /var/lib/clamav/* && \
    echo "Win.Test.EICAR_NDB-1:0:0:58354f2150254041505b345c505a58353428505e2937434329377d2445494341522d5354414e444152442d414e544956495255532d544553542d46494c452124482b482a" > /var/lib/clamav/test.ndb && \
    echo "45056:f9b304ced34fcce3ab75c6dc58ad59e4d62177ffed35494f79f09bc4e8986c16:Win.Test.EICAR_MSB-1" > /var/lib/clamav/test.msb && \
    echo "45056:3ea7d00dedd30bcdf46191358c36ffa4:Win.Test.EICAR_MDB-1" > /var/lib/clamav/test.mdb && \
    echo "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f:68:Win.Test.EICAR_HSB-1" > /var/lib/clamav/test.hsb && \
    echo "44d88612fea8a8f36de82e1278abb02f:68:Win.Test.EICAR_HDB-1" > /var/lib/clamav/test.hdb && \
    mkdir -p /var/run/clamd.scan && \
    chown -R containeruser: /var/run/clamd.scan
COPY clamd.conf /etc/clamd.d/scan.conf

# Set the user back to a non-root user like the s2i run script expects
# When creating files inside the docker container, this will also prevent the files being owned
# by the root user, which would cause issues if running on a Linux host machine
USER containeruser

CMD clamd && /usr/libexec/s2i/run
