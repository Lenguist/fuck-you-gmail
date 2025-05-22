Primary goal: change how i interact with emails.

Important emails get lost and reading through all of them can be a chore.

Solution: instead of reading through all emails, you chat with your inbox.

Ideal end product is sort of an assistant that i can ask stuff like "catch me up on unread emails" or "respond to email X with Y"

Kind of like email filter you dont have to set up yourself.
Helps to put hte most urgent messages on top.

Primary use case: many emails. So more than 128k to work through.

Weekly email digest is the first iteration.

Then i can add more functionality to interact and better summarization.

# Email Summarizer Project

## Overview
The **Email Summarizer** is a service that pulls emails for each user, summarizes them based on user preferences, and sends a daily digest email. Users can sign up using their Gmail accounts, choose the time they want to receive their daily digest, and customize how the summarization works.

---

## Project Structure

### 1. **Local Structure**
This is the initial structure where data was stored locally in `.txt` files.

- **Data Storage**:
  - User emails and preferences are stored in a local folder.
  
  **Example Folder Structure**:
emails/ user_id/ email1.txt email2.txt ... daily_digest.txt # Stores user preferences and summarization prompts

markdown
Copy code

- **Sign-up & Preferences**:
- Users sign up via a local Flask app, and their preferences (e.g., the time to send the daily digest) are stored in `daily_digest.txt`.

- **Email Pull & Summarization**:
- Gmail API is used to pull emails, and summarization is handled locally.

- **Deployment**:
- Flask is run locally, and Mailgun is used for sending emails.

---

### 2. **AWS Deployment Plan**
This plan scales the project to handle multiple users with fast data access using AWS services.

- **Data Storage**:
- Emails and user preferences are stored in **AWS S3**.

**Example S3 Folder Structure**:
emails/ user_id/ email1.txt email2.txt ... daily_digest.txt # Stores user preferences and summarization prompts

markdown
Copy code

- **AWS Services**:
- **EC2**: Hosts the Flask app that serves the website and handles user interactions.
- **S3**: Stores user emails and preferences.
- **Mailgun**: Handles sending daily digest emails.
- **AWS Lambda (Optional)**: Can be used to pull emails and generate summaries at specific times.

- **Authentication**:
- Uses **Google OAuth 2.0** for user authentication, allowing them to sign in using Gmail.

- **Sign-up Page**:
- Users sign up, authenticate with Gmail, and choose their daily digest time.
- Flask serves a basic **HTML/CSS** landing page.

- **Data Storage**:
- For each user, an S3 folder is created to store their emails and their `daily_digest.txt`, which includes their preferences for summarization.

- **Summary Scheduling**:
- **Celery** (or **AWS Lambda**) is used to schedule pulling emails and sending summaries at the user-specified time.

- **Deployment**:
- The Flask app is deployed on an **EC2** instance.
- **Nginx** is used as a reverse proxy, and **SSL** is set up using **Certbot** for HTTPS.
- User emails and preferences are stored in **AWS S3**.

---

## Setup Instructions

### Local Development

1. Clone the repository:
 ```bash
 git clone https://github.com/your-repo/email-summarizer.git
 cd email-summarizer
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Run the Flask server:

bash
Copy code
python app.py
To send email summaries locally, ensure you have a Mailgun API Key and update send_summary_email().

AWS Deployment
Set up AWS EC2:

Launch an EC2 instance and SSH into the server.
Install Python, Flask, and necessary dependencies on the server.
Configure S3:

Create an S3 bucket to store user emails and daily digest files.
Use boto3 to interact with S3 from your Flask app.
Deploy Flask App:

Use Nginx as a reverse proxy to serve the Flask app.
Set up SSL using Certbot for HTTPS.
Set up Email Delivery:

Use Mailgun for sending the daily email summaries.
Configure Celery or CloudWatch to schedule email sending based on user preferences.
Roadmap
Add a settings page for users to update their email summarization preferences.
Improve the summarization algorithm for better user-customized results.
Implement monitoring and logging for better tracking of user emails and summary delivery.
javascript
Copy code

This `README.md` provides both the local and AWS deployment structures, as well as setup instructions for both environments.