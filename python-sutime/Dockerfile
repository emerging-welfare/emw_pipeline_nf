FROM rappdw/docker-java-python:latest

MAINTAINER Abdulrahman Alabrash <aalabrash18@ku.edu.tr>

WORKDIR /usr/src/app
RUN apt-get update
RUN apt-get -y install g++ python-dev python3-dev ant
RUN apt-get install -y software-properties-common

RUN apt-get install --yes --no-install-recommends \
    wget \
    vim \  
    git \
    sudo \
    maven \  
    tmux \ 
    locales \
    cmake \
    gcc-multilib \
    build-essential \
    apt-utils


RUN pip install --upgrade pip   
ENV _JAVA_OPTIONS="-Xmx6g"
COPY . . 
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN git clone https://github.com/FraBle/python-sutime 
RUN cd python-sutime  && mvn dependency:copy-dependencies -DoutputDirectory=./jars && cd .. && mv -v python-sutime/* ./temporalTagger
RUN rm -rf python-sutime 
WORKDIR /usr/src/app/temporalTagger 
CMD [ "python", "ttFlask.py" ]


