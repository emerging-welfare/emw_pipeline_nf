# Set the base image to Ubuntu
FROM rappdw/docker-java-python:latest
#FROM debian:jessie
# File Author / Maintainer
MAINTAINER Abdulrahman Alabrash <aalabrash18@ku.edu.tr>

#RUN printf "deb http://archive.debian.org/debian/ jessie main\ndeb-src http://archive.debian.org/debian/ jessie main\ndeb http://security.debian.org jessie/updates main\ndeb-src http://security.debian.org jessie/updates main" > /etc/apt/sources.list
RUN apt-get update
# RUN apt-get -y install default-jre 
#RUN apt-get -y install default-jdk
RUN apt-get -y install g++ python-dev python3-dev ant

RUN apt-get install -y software-properties-common
# install miniconda 
# conda create --name nextflow python=3.6.4
# conda activate nextflow
# conda install -c bioconda nextflow==18.10.1 && ./nextflow ./nextflow_dir/example

#RUN printf "deb http://archive.debian.org/debian/ jessie main\ndeb-src http://archive.debian.org/debian/ jessie main\ndeb http://security.debian.org jessie/updates main\ndeb-src http://security.debian.org jessie/updates main" > /etc/apt/sources.list

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
    build-essential 



 RUN pip install --upgrade pip
 #RUN git clone https://github.com/emerging-welfare/nextflow_test
 COPY . nextflow_test
 RUN pip install -r /nextflow_test/requirements.txt 
 RUN python -c "import nltk;nltk.download('popular', halt_on_error=False)"
 RUN git clone https://github.com/Jekub/Wapiti && cd Wapiti && make install
#  RUN git clone https://github.com/chentinghao/download_google_drive.git
#  RUN python download_google_drive/download_gdrive.py 13O8L8cauTF1ZgtVkS-XahwA20v_tglyq ./jars.zip
#  RUN unzip jars.zip -d ./nextflow_test/bin/jars
#  RUN sudo rm jars.zip
#  RUN sudo rm -rf download_google_drive

WORKDIR nextflow_test
# #RUN wget http://www.us.apache.org/dist/tomcat/tomcat-6/v6.0.44/bin/apache-tomcat-6.0.44.tar.gz

# # clone from github
# RUN git clone https://github.com/emerging-welfare/nextflow_test
#COPY ./ ./

#PYTHON3 PIP

#RUN  python -c "import nltk;nltk.download('stopwords');nltk.download('wordnet');nltk.download('averaged_perceptron_tagger');nltk.download('punkt');nltk.download('maxent_ne_chunker');nltk.download('words')"

# Install OpenJDK-8
# RUN echo "deb http://http.debian.net/debian jessie-backports main" > /etc/apt/sources.list.d/jessie-backports.list \
#     && apt-get update -qq \
#     && apt install -t jessie-backports -y openjdk-8-jdk ca-certificates-java \
#     && /usr/sbin/update-java-alternatives -s java-1.8.0-openjdk-amd64 \
#     && apt-get install -y maven

# RUN apt-get update && \
#     apt-get install -y openjdk-8-jdk && \
#     apt-get install -y ant && \
#     apt-get clean;

# # Fix certificate issues
# RUN apt-get update && \
#     apt-get install ca-certificates-java && \
#     apt-get clean && \
#     update-ca-certificates -f;

# # Setup JAVA_HOME -- useful for docker commandline
# ENV JAVA_HOME /usr/lib/jvm/java-8-openjdk-amd64/
# RUN export JAVA_HOME

# #Install Java
# # RUN software-properties-common && apt-get upgrade && apt-get update
# # RUN add-apt-repository ppa:webupd8team/java && apt-get update && apt-get install -y oracle-java8-installer
#RUN apt-get -y install default-jre

# #Install Jar of SUtime
# RUN git clone https://github.com/FraBle/python-sutime |cd python-sutime| mvn dependency:copy-dependencies -DoutputDirectory=./jars
# RUN mv -t ../  jars java sutime