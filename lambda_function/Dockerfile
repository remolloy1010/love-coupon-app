# Use an official Python runtime as a parent image
FROM python:3.11-slim-bullseye

# Set the working directory in the container
WORKDIR .

# Copy the local Lambda function files into the container
COPY lambda_function.py .

# Install any necessary dependencies
# If you have a requirements.txt file, uncomment the next line
COPY requirements.txt . 

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Set the Lambda runtime environment variables (if needed)
ENV AWS_REGION us-west-2

ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "lambda_function.lambda_handler" ]
