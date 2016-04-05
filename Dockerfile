# Set the base image to Ubuntu
FROM ubuntu

# File Author / Maintainer
MAINTAINER Maintainer Shan Randhawa

# Add the application resources URL
RUN echo "deb http://archive.ubuntu.com/ubuntu/ $(lsb_release -sc) main universe" >> /etc/apt/sources.list

# Update the sources list
RUN apt-get update

# Install basic applications
RUN apt-get install -y tar git curl nano wget dialog net-tools build-essential libmysqlclient-dev

# Install Python and Basic Python Tools
RUN apt-get install -y python=2.7.5-5ubuntu3 python-dev python-distribute python-pip

RUN apt-get update

RUN apt-get install -y python-lxml=3.3.3-1ubuntu0.1

RUN apt-get update

# Copy the application folder inside the container
ADD /arctic /arctic

# Get pip to download and install requirements:
RUN pip install -r /arctic/requirements.txt

# Expose ports
EXPOSE 80

# Set the default directory where CMD will execute
WORKDIR /arctic

ENV DB_HOST 127.0.0.1
ENV DB_PORT 3306
ENV DB_USER root
ENV DB_PASSWORD test
ENV DB arctic
ENV SESSION_SECRET_KEY secret
ENV LOG_FILE_PATH /docs/logs/

# Set the default command to execute
# when creating a new container
# i.e. using CherryPy to serve the application
CMD python server.py
