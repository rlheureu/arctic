# Set the base image to Ubuntu
FROM ubuntu:14.04

# File Author / Maintainer
MAINTAINER Maintainer Shan Randhawa

# Add the application resources URL

# Update the sources list
RUN apt-get update -y

# Install basic applications
RUN apt-get install -y tar git curl nano wget dialog net-tools build-essential libmysqlclient-dev

# Install Python and Basic Python Tools
RUN apt-get install -y python=2.7.5-5ubuntu3 python-dev python-distribute python-pip

RUN apt-get install -y python-lxml=3.3.3-1ubuntu0.1

# Copy the application folder inside the container
ADD . /arctic

# Get pip to download and install requirements:
RUN pip install -r /arctic/requirements.txt

# Expose ports
EXPOSE 80

# Set the default directory where CMD will execute
WORKDIR /arctic

ENV ARCTIC_DEV_UNAME gamer
ENV ARCTIC_DEV_PWD password
ENV DB_HOST 127.0.0.1
ENV DB_PORT 3306
ENV DB_USER root
ENV DB_PASSWORD test
ENV DB arctic
ENV SESSION_SECRET_KEY secret
ENV LOG_FILE_PATH /docs/logs/
ENV FULL_APP_URL amdahlcube.com
ENV APP_EMAILER_ADDRESS shanrandhawa@gmail.com
ENV APP_EMAILER_PASSWORD asdf

# Set the default command to execute
# when creating a new container
# i.e. using CherryPy to serve the application
CMD python server.py
