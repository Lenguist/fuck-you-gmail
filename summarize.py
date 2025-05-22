from openai import OpenAI

def produce_daily_digest(specific_date, email_contents):
    if not email_contents:
        raise FileNotFoundError(f"No emails found for {specific_date.strftime('%Y-%m-%d')}.")

    # Load the summarization prompt
    with open('digest_prompt.txt', 'r') as f:
        prompt = f.read()

    # Combine email content into a single string
    email_content = email_contents

    # Summarize using OpenAI API
    client = OpenAI()
    completion = client.chat.completions.create(
        model="gpt-4o-mini",  # Replace with the correct model
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"{prompt}\n{email_content}"}
        ]
    )

    # Return the generated summary
    return completion.choices[0].message.content

