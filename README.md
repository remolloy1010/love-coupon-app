# Love Coupon App

## Steps to Reproduce

### Create Virtual Environment and Activate

1. Install virtualenv (if applicable)

```
python3.9 -m pip install virtualenv
```

2. Create virtual environment

```
python3.9 -m virtualenv venv
```

3. Activate virtual environment

```
source venv/bin/activate
```

### AWS Set Up

1. Install AWS CLI for Mac: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html

2. Set up Access Key ID and Secret Access Key by navigating to account --> security credentials and create Access Key ID and Secret Access Key: https://us-east-1.console.aws.amazon.com/iam/home#/security_credentials

3. Run `aws configure` and enter credentials created in step 2

4. Log in to ECR from CLI:

```
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 015172458433.dkr.ecr.us-west-2.amazonaws.com
```

### Create AWS Elastic Container Registry (ECR) Repository

1. Log in to AWS account

2. Navigate to ECR resource

3. Create repository named `dreams-project-repo`

### Build Container and Run

Be sure to be in lambda_function container:

1. Build Docker container

```
docker build -t 015172458433.dkr.ecr.us-west-2.amazonaws.com/love_coupon_lambda:latest .
```

2. Run Docker container

```
docker run -p 8050:8050 love_coupon_app
```

3. Tag Docker container

```
docker tag love_coupon_lambda:latest 015172458433.dkr.ecr.us-west-2.amazonaws.com/love_coupon_lambda:latest
```

4. Push to ECR repository

```
docker push 015172458433.dkr.ecr.us-west-2.amazonaws.com/love_coupon_lambda:latest
```

### Push to AWS Elastic Container Registry (ECR)

```

```

### Set up AWS Lightsail resource and deploy container to Lightsail

1. Create a container service in LightSail. Choose the region, the power and node size to be allocated to the application, and the domain name.

2. Create your first deployment. Navigate to the "Deployment" tab to create your deployment.

Follow the steps in this resource to get started: https://www.youtube.com/watch?v=RhcR5LaRXIQ

### AWS CDK

Prerequisites:

- Ensure npm is installed. In the CLI, run `npm --version` and make sure you have version X, or install using this link: https://nodejs.org/en/download/
- Install AWS CDK using npm (easiest way): `npm install -g aws-cdk`

### Deploying to EC2

https://adzic-tanja.medium.com/deploying-a-streamlit-app-using-docker-aws-ecr-and-ec2-ad6c15a0b225
https://www.youtube.com/watch?v=Jc5GI3v2jtE

### How to Update ECS Deployment When ECR Image Updates

https://stackoverflow.com/questions/34840137/how-do-i-deploy-updated-docker-images-to-amazon-ecs-tasks

Force redeployment:

```
aws ecs update-service --force-new-deployment --service love-coupon-service --cluster love-coupon-fargate
```

### Register a domain name with Route 53

1. Navigate to Route 53 in AWS
2. Choose a domain name and purchase
3.

### Set up Google Auth

1. Follow this Python quickstart guide: https://developers.google.com/calendar/api/quickstart/python
2. Create a project
3. Enable the API
4. Configure the OAuth consent screen. Select "External User Type"
5. Add the developer email address(es)
6. Add the following scopes: https://www.googleapis.com/auth/calendar, https://www.googleapis.com/auth/calendar.readonly, https://www.googleapis.com/auth/calendar.events
7. Add test users email addresses
8. Authorize credentials for application
9. Create OAuth Client ID credentials for desktop application
10. Download the JSON and save as 'credentials.json' to your working directory
11. Test running quickstart.py
12. A pop up window will say the app hasn't been verified. Click "Continue" button on the left.
13. Another pop-up window will come up. Click "Continue"
14. When you run the quickstart.py, a tokens.json file will be created with the credentials. Save the credentials to AWS Secrets Manager:

### Save AWS Secrets Manager

1. Go to AWS Secrets Manager
2. Select "Store a new key"
3. Click "Other credentials...."
4. Disable automatic credential rotation.

5. Create service account
6. Give owner access to the project
7. Create keys and save json file as service-account-key.json
8. Add the authenticate function to replace the credentials with the token stuff
9. The target calendar must share access to the service account.

test payload:
{
"title" : "Weeding",
"description" : "...doesn't rock",
"selected_start_date": "2024-02-16",
"selected_start_time": "15:00:00",
"selected_end_date": "2024-02-17",
"selected_end_time": "15:00:00"
}

## Lambda Function

The `love_coupon_lambda` lambda function gets the Google Calendar API credentials from AWS Secrets Managers, authenticates, and then creates a Google Calendar event when the coupon is redeemed on the UI.

1. Login to ECR

```
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 015172458433.dkr.ecr.us-west-2.amazonaws.com
```

2. Build Docker image

```
docker build -t 015172458433.dkr.ecr.us-west-2.amazonaws.com/love_coupon_lambda:latest .
```

3. Push to ECR repository

```
docker push 015172458433.dkr.ecr.us-west-2.amazonaws.com/love_coupon_lambda:latest
```

## Streamlit App

1. Login to ECR

```
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 015172458433.dkr.ecr.us-west-2.amazonaws.com
```

2. Build Docker image

```
docker build -t  015172458433.dkr.ecr.us-west-2.amazonaws.com/love-coupon-app:latest .
```

3. Push to ECR repository

```
docker push 015172458433.dkr.ecr.us-west-2.amazonaws.com/love-coupon-app:latest
```

https://adzic-tanja.medium.com/deploying-a-streamlit-app-using-docker-aws-ecr-and-ec2-ad6c15a0b225
https://www.youtube.com/watch?v=DflWqmppOAg&t=1148s

1. Connect to EC2 instance

2. run `sudo yum update`
3. run `sudo yum upgrade`
4. run `sudo yum install docker`
5.

From EC2 Instance:

1.

sudo aws ecr get-login-password --region us-west-2 | sudo docker login --username AWS --password-stdin 015172458433.dkr.ecr.us-west-2.amazonaws.com

sudo service docker start
sudo chkconfig docker on # For Amazon Linux

## How to Deploy Docker Image to EC2

1. Connect to Instance

2. Run `sudo yum update` (if Linux)

3. Run `sudo yum upgrade`

4. Run `sudo yum install docker`

5. After installing Docker, start the Docker service and enable it to start on boot:

```
sudo service docker start
sudo chkconfig docker on
```

6. Verify that docker was successfully installed by running `docker --version`

7. (Not sure if this is necessary) Copy short term credentials to terminal to authenticate

8. Run the following to login to the ECR

```
sudo aws ecr get-login-password --region us-west-2 | sudo docker login --username AWS --password-stdin 015172458433.dkr.ecr.us-west-2.amazonaws.com
```

9. Pull the latest Docker image from the ECR

```
sudo docker pull 015172458433.dkr.ecr.us-west-2.amazonaws.com/love-coupon-app:latest
```

10. Run Docker image in the EC2

```
sudo docker run -d -p 8501:8501 015172458433.dkr.ecr.us-west-2.amazonaws.com/love-coupon-app:latest
```

11. Go back to the console for the EC2 instance, and copy-paste the public IP address to a browser. Add the port number:

```
http://34.220.178.95:8501/
```

12. To ensure your app is always running, even when you exit the EC2 instance terminal, run the following:

```
nohup
```

13. To kill the port on the terminal, run the following to get the list of ports running:

```
sudo lsof -i:8501
```

14. Then run the following to kill the open ports:

```
sudo kill <PID>
```

15. Restart Docker container:

```
sudo systemctl restart docker
```

16. Rerun Docker container with latest changes pulled down:

```
sudo docker run -d -p 8501:8501 015172458433.dkr.ecr.us-west-2.amazonaws.com/love-coupon-app:latest
```

## Updating Docker container with latest image:

1. Connect into EC2 instance.

2. Pull the latest Docker image from the ECR

```
sudo docker pull 015172458433.dkr.ecr.us-west-2.amazonaws.com/love-coupon-app:latest
```

3. Restart Docker container:

```
sudo systemctl restart docker
```

4. Rerun Docker container with latest changes pulled down:

```
sudo docker run -d -p 8501:8501 015172458433.dkr.ecr.us-west-2.amazonaws.com/love-coupon-app:latest
```

## Adding SSL Certificate:

https://www.youtube.com/watch?v=Ronr-B_bkGg&t=458s

sudo yum update
sudo yum install nginx

sudo nano /etc/nginx/conf.d/streamlit.conf

server {
listen 80;
server_name benslovecoupon.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

}

sudo systemctl restart nginx

In the nano text editor, pressing Ctrl + O (the letter O, not zero) allows you to save the changes, and then press Enter to confirm the filename. After that, you can press Ctrl + X to exit the editor. So, after making changes to the configuration file, you should press Ctrl + O, then Enter, and finally Ctrl + X to save the changes and exit the editor.

server {
listen 80;
server_name benslovecoupon.com;

    location / {
        proxy_pass http://benslovecoupon:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

}

# Troubleshooting

- SELinux was denying access to Nginx:
  type=AVC msg=audit(1708646412.564:41020): avc: denied { name_connect } for pid=67146 comm="nginx" dest=8501 scontext=system_u:system_r:httpd_t:s0 tcontext=system_u:object_r:unreserved_port_t:s0 tclass=tcp_socket permissive=1

To fix it, I need to allow Nginx to access port 8501

https://discuss.streamlit.io/t/running-streamlit-on-aws-ec2-handling-port-issues-port-80-port-8501-nginx/29902/2

## IT WORKEDDDDDD!!!!!!!!!

In addition to the Nginx steps above, run this:

Install `iptables`, which is used for configuring and managing packet filtering rules in the Linux kernel:

```
sudo yum install iptables
```

```
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8501
```

-t nat: Specifies the table to which the rule should be added (in this case, the NAT table).
-A PREROUTING: Appends the rule to the PREROUTING chain, which processes packets before routing.
-p tcp: Specifies that the rule applies to TCP packets.
--dport 80: Specifies the destination port (port 80).
-j REDIRECT --to-port 8501: Redirects packets matching the rule to port 8501.

With this configuration, any incoming HTTP traffic to port 80 will be redirected to port 8501, where your application is running. This allows users to access your application using the standard HTTP port without specifying the port number in the URL.

https://www.youtube.com/watch?v=3j33lNzMZlM (THE MOST HELPFUL VIDEO!!!!)
https://repost.aws/it/questions/QUgbVAL02NS6uMH6Emt07jaA/redirecting-port-443-to-8501-on-ec2?sc_ichannel=ha&sc_ilang=en&sc_isite=repost&sc_iplace=hp&sc_icontent=QUgbVAL02NS6uMH6Emt07jaA&sc_ipos=8
https://stackoverflow.com/questions/70177733/the-streamlit-app-stops-with-please-wait-and-then-stops

## Application Load Balancer

I followed this tutorial, but with one additional change: I had to update my HTTPS 443 listener to forward traffic to HTTP port 8501 because that is where my server was running for my Streamlit app. So I created a target group with HTTP port 8501, and pointed my listener there.

https://www.youtube.com/watch?v=3j33lNzMZlM (THE MOST HELPFUL VIDEO!!!!)

1. Create Application Load Balancer.

2. Set up an HTTPS listener for Port 443. Create a target group that forwards the traffic from port 443 to port 8501 where the server is located.

3. Set up an HTTP listener for Port 80 that redirects traffic to port 443 (for HTTPS traffic only).

4. Save listeners and attach load balancer to EC2 instance.

5. In Route 53, create a Type A record. Toggle on "Alias" and select Classic and Application Load Balancers, the region (us-west-2), and select the load balancer that has been created. You may have to delete other Type A records if they were created previously.

Note: for some reason I have to go on incognito because my browser keeps automatically adding :8501 to the end of my domain name. Might need to clear cache...
