FROM terraref/terrautils:1.5
LABEL maintainer="Chris Schnaufer <schnaufer@email.arizona.edu>"

# Install any users
RUN useradd -u 49044 extractor \
    && mkdir /home/extractor \
    && mkdir /home/extractor/sites

RUN chown -R extractor /home/extractor \
    && chgrp -R extractor /home/extractor 

# install and upgrade OS packages
RUN apt install -y imagemagick gdal-bin libgdal-dev

# install and upgrade pip and other python packages
RUN pip install --no-cache-dir --upgrade pip 

RUN pip install --upgrade numpy && \
    pip install --upgrade dbfread && \
    pip install --upgrade pyclowder && \
    pip install gdal  && \
    pip install --upgrade cryptography \
    pip install --upgrade --ignore-installed enum34 terrautils

COPY extractor_base.py entrypoint.sh /home/extractor/

# command to run when starting docker
USER extractor
ENTRYPOINT ["/home/extractor/entrypoint.sh"]
CMD ["extractor"]

# Setup environment variables. These are passed into the container. You can change
# these to your setup. If RABBITMQ_URI is not set, it will try and use the rabbitmq
# server that is linked into the container. MAIN_SCRIPT is set to the script to be
# executed by entrypoint.sh
ENV RABBITMQ_EXCHANGE="terra" \
    RABBITMQ_VHOST="%2F" \
    RABBITMQ_QUEUE="terra.dronepipeline.extractor" \
    MAIN_SCRIPT="extractor_base.py"
