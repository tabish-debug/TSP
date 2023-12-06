FROM python:3.11.6
WORKDIR /JBTC
COPY ./requirements.txt /JBTC/requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r /JBTC/requirements.txt
COPY . /JBTC/