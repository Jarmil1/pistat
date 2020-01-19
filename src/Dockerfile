# Use an official Python runtime as a parent image

FROM python:3.6.7

WORKDIR /metriky

COPY . /metriky

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Run command when the container launches. Parametr -u je pro unbuffered output prikazu print()
CMD ["python", "-u", "pistat.py", "-rw"]
