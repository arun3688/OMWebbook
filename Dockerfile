FROM ubuntu

RUN apt-get update 

# Install wget
RUN apt-get install -y wget


# Add OpenModelica stable build
RUN for deb in deb deb-src; do echo "$deb http://build.openmodelica.org/apt `lsb_release -cs` stable"; done | sudo tee /etc/apt/sources.list.d/openmodelica.list
RUN wget -q http://build.openmodelica.org/apt/openmodelica.asc -O- | sudo apt-key add - 

# Update index (again)
RUN apt-get update

# Install OpenModelica
RUN apt-get install -y openmodelica

RUN apt-get install -y python-pip python-dev build-essential 
RUN apt-get install -y omniidl \
                       omniidl-python \
                       omniorb \
                       omniorb-idl \
	                   git \
					   python-numpy \
                       nginx \
                       supervisor \
                       python-omniorb 
                     			   
RUN sudo pip install git+https://github.com/arun3688/OMPython

ADD . /Flasktest
WORKDIR /Flasktest

RUN pip install futures
RUN pip install gunicorn 

RUN pip install -r requirements.txt
#EXPOSE 5000

# Setup nginx
RUN rm /etc/nginx/sites-enabled/default
COPY flask.conf /etc/nginx/sites-available/
RUN ln -s /etc/nginx/sites-available/flask.conf /etc/nginx/sites-enabled/flask.conf
RUN echo "daemon off;" >> /etc/nginx/nginx.conf


# Setup supervisord
RUN mkdir -p /var/log/supervisor
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf
#COPY gunicorn.conf /etc/supervisor/conf.d/gunicorn.conf

# Start processes
CMD ["supervisord","-c","/etc/supervisor/conf.d/supervisord.conf"]

#CMD ["sudo","-u","nobody","python","index.py"]
#CMD ["sudo","-u","nobody","gunicorn","-b 0.0.0.0:5000","index:app"]
