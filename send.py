import requests
from datetime import datetime
from gmail_auth import authenticate_gmail
# Update this call wherever you use authenticate_gmail
service, recipient_email = authenticate_gmail()

def send_summary_email(summary, recipient_email):

    
    return requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={"from": f"Email Summarizer <{sender}>",
              "to": [recipient_email],  # Use the authenticated user's email as the recipient
              "subject": "Your Daily Email Summary",
              "text": summary})

def send_specific_day_summary(summary, specific_date):

    return requests.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={"from": f"Email Summarizer <{sender}>",
              "to": [recipient],
              "subject": f"Email Summary for {specific_date.strftime('%Y-%m-%d')}",
              "text": summary})
