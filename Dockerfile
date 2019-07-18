FROM rappdw/docker-java-python:latest

MAINTAINER Abdulrahman Alabrash <aalabrash18@ku.edu.tr>

RUN apt-get update
RUN apt-get -y install g++ python-dev python3-dev ant
RUN apt-get install -y software-properties-common

RUN apt-get install --yes --no-install-recommends \
    wget \
    git \
    locales \
    cmake \
    gcc-multilib \
    build-essential \
    apt-utils

ENV _JAVA_OPTIONS="-Xmx2g"
RUN git clone https://github.com/emerging-welfare/emw_pipeline_nf.git
RUN pip3 install --upgrade pip
RUN pip2 install --upgrade pip

# nextflow installation
ENV NXF_VER=19.04.1
RUN wget -qO- https://get.nextflow.io | bash
RUN mv nextflow ./bin
RUN nextflow

# Extract & Doc Preprocess Dependencies
RUN cd /emw_pipeline_nf && git checkout comprehensive && pip2 install --no-cache-dir -r requirements2.txt && pip3 install --no-cache-dir -r requirements.txt
RUN git clone https://github.com/OsmanMutlu/python-boilerpipe.git && cd python-boilerpipe.git && python2 setup.py install && cd .. && rm -rf python-boilerpipe

# Tokenizer
RUN python -c "import nltk;nltk.download('popular', halt_on_error=False)"

# DTC depenedecy
RUN git clone https://github.com/Jekub/Wapiti && cd Wapiti && make install

RUN echo "cd /emw_pipeline_nf && git checkout comprehensive && git pull origin comprehensive" >> ~/.bashrc
RUN echo "nohup python3 /emw_pipeline_nf/bin/classifier/classifier_flask.py 2> /dev/null &" >> ~/.bashrc
RUN echo "cd emw_pipeline_nf" >> ~/.bashrc
RUN echo "export PYTHONPATH=$PYTHONPATH:/new_pipeline/bin" >> ~/.bashrc