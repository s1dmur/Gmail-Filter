import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def move_to_trash_with_modify(service, user_id, msg_id):
    try:
        service.users().messages().modify(
            userId=user_id,
            id=msg_id,
            body={
                "removeLabelIds": [],
                "addLabelIds": ["TRASH"]
            }
        ).execute()
        

    except Exception as error:
        print(f'An error occurred: {error}')

def delete_emails(service, user_id, sender=None, keywords=None, whitelist=None):
    try:
        query_parts = []
        
        if sender:
            query_parts.append(f'from:({sender})')
        
        if keywords:
            keyword_query = ' OR '.join(f'"{keyword}"' for keyword in keywords)
            query_parts.append(f'({keyword_query})')
        
        if not query_parts:
            raise ValueError("At least one of sender or keywords must be specified")
        
        query = ' AND '.join(query_parts)
        print(f"Executing query: {query}")
        
        # Pagination for retrieving messages
        next_page_token = None
        while True:
            results = service.users().messages().list(userId=user_id, q=query, pageToken=next_page_token).execute()
            messages = results.get('messages', [])
            next_page_token = results.get('nextPageToken')

            if not messages:
                print('No more messages found.')
                break

            for message in messages:
                # Get the message details to retrieve the sender
                msg = service.users().messages().get(userId=user_id, id=message['id'], format='metadata').execute()
                headers = msg['payload']['headers']
                msg_sender = next((header['value'] for header in headers if header['name'] == 'From'), None)

                # Check if the sender is in the whitelist
                if whitelist and any(whitelisted in msg_sender for whitelisted in whitelist):
                    print(f'Message from {msg_sender} is whitelisted and will not be trashed.')
                    continue

                # Move to trash
                msg_id = message['id']
                move_to_trash_with_modify(service, user_id, msg_id)
                print(f'Message ID: {msg_id} from {msg_sender} moved to trash.')

            if not next_page_token:
                break

    except Exception as error:
        print(f'An error occurred: {error}')

def main():
    service = get_gmail_service()
    user_id = 'me'  # 'me' represents the authenticated user
    
    # Example whitelist of senders
    whitelist = ['studentlife@stonybrook.edu']  # Add specific emails or domains here
    
    # Example usage: delete all emails from a specific sender
    delete_emails(service, user_id, keywords = ['steam wishlist'])

if __name__ == '__main__':
    main()
    #need to create gui
    #need to add whitelist of keywords
    #need to add sentiment analysis
