import os
from twilio.rest import Client
from dotenv import load_dotenv
from app.utils.helper_functions import has_user_submitted_tips
from app.models import User
from app import create_app, db
import app

# Load .env from root directory
#load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv()

account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)

def send_msg(recipient, msg):
    message = client.messages.create(
        body=msg,
        from_='+19036485985',  # Your Twilio trial number
        to= f'+61{recipient}'      # Your verified mobile number (Australia example)
    )

    print(f"Message sent! SID: {message.sid}")


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        msg='''
        ⚠️ Hey! This is your weekly tipping reminder. ⚠️ 
        Don’t forget to submit by 5PM Thursday!
        All participants who havnt submited by then will automatically be given the home teams 
        '''
        users = User.query.all()
        havnt_submitted = []
        for user in users:
            if (not has_user_submitted_tips(user.id)) and (user.phone_number is not None):
                send_msg(user.phone_number,msg)
                print(f"Message reminder sent to:\n {user.username}")
                havnt_submitted.append(user.username)
        recipients = "\n ".join(havnt_submitted)
        send_msg('488534484',f'reminders where sent to:\n {recipients}')
        
    
        