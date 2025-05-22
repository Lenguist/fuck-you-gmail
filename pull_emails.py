from datetime import datetime, timedelta
from gmail_auth import authenticate_gmail

def pull_emails_for_specific_day(specific_date):
    # Authenticate the user via Gmail
    service, _ = authenticate_gmail()

    # Ensure specific_date is a datetime.date object
    if isinstance(specific_date, datetime):
        specific_date = specific_date.date()

    # Container for email content
    email_content_list = []
    
    # Loop through all 24 hours of the specified day and pull emails
    for hour in range(24):
        start_time = datetime(specific_date.year, specific_date.month, specific_date.day, hour)
        end_time = start_time + timedelta(hours=1)

        # Convert to Unix timestamps
        start_timestamp = int(start_time.timestamp())
        end_timestamp = int(end_time.timestamp())

        # Query Gmail for emails in the specified timeframe
        query = f'after:{start_timestamp} before:{end_timestamp}'
        messages = service.users().messages().list(userId='me', q=query, labelIds=['INBOX']).execute().get('messages', [])
        
        # If no emails found, continue to the next hour
        if not messages:
            continue

        # Fetch content for each message
        for message in messages:
            msg = service.users().messages().get(userId='me', id=message['id']).execute()
            snippet = msg.get('snippet', 'No content')
            email_content_list.append(snippet)

    # Combine all email content into one string
    combined_email_content = "\n\n".join(email_content_list)

    # Print the length of the combined email content
    print(f"Total length of combined emails: {len(combined_email_content)}")

    return combined_email_content
