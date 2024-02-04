FROM conda/miniconda3

RUN apt-get -y update && apt-get -y install curl

RUN conda update -n base -c defaults conda

RUN conda install -c conda-forge ta-lib &&  \
    conda install -c anaconda pandas && \
    conda install -c anaconda numpy && \
    conda install -c conda-forge pyyaml && \
    conda install -c conda-forge munch && \
    conda install -c anaconda requests && \
    conda install -c anaconda flask && \
    conda install -c anaconda flask-cors && \
    conda install -c conda-forge flask-sqlalchemy && \
    conda install -c anaconda sqlalchemy

RUN pip install binance-futures-connector
