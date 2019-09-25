FROM terraref/terrautils:1.5
LABEL maintainer="Chris Schnaufer <schnaufer@email.arizona.edu>"

# Install any users
RUN useradd -u 49044 extractor \
    && mkdir /home/extractor \
    && mkdir /home/extractor/sites

RUN chown -R extractor /home/extractor \
    && chgrp -R extractor /home/extractor 

# install and upgrade OS packages
RUN apt-get update

RUN apt install -y imagemagick \
        gdal-bin \
        libgdal-dev \
        python-gdal \
        python-tk

# install and upgrade pip and other python packages
RUN python -m pip install --no-cache-dir --upgrade pip 

RUN python -m pip install --upgrade numpy && \
    python -m pip install --upgrade laspy && \
    python -m pip install gdal  && \
    python -m pip install --upgrade cryptography && \
    python -m pip install --upgrade --ignore-installed enum34 terrautils && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY extractor_base.py /home/extractor/

RUN chmod +x /home/extractor/extractor_base.py

# command to run when starting docker
USER extractor
ENTRYPOINT ["/home/extractor/extractor_base.py"]
CMD ["", "", "", "", ""]

