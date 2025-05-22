import os
from datetime import datetime, timedelta
from send import send_specific_day_summary
from summarize import produce_daily_digest
from pull_emails import pull_emails_for_specific_day

def test_retroactively(N):
    today = datetime.utcnow()
    print(f"Doing retroactive test for {N} days")

    for i in range(1, N + 1):
        specific_date = today - timedelta(days=i)
        print(f"\nSimulating email pulls for {specific_date.strftime('%Y-%m-%d')}...")

        # Pull emails for the specified day
        email_content = pull_emails_for_specific_day(specific_date)

        # Summarize emails for the previous day
        summary = produce_daily_digest(specific_date, email_content)
        # print(f"Summary for {specific_date.strftime('%Y-%m-%d')}:\n{summary}")

        # Send the summary via email
        response = send_specific_day_summary(summary, specific_date)
        if response.status_code == 200:
            print(f"Summary for {specific_date.strftime('%Y-%m-%d')} sent successfully!")
        else:
            print(f"Failed to send summary for {specific_date.strftime('%Y-%m-%d')}. Status code: {response.status_code}")

# Run the retroactive email pull and summarization for the last 2 days
test_retroactively(2)
