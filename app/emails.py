# emails.py
from django.core.mail import send_mail, EmailMessage
from django.core.mail import get_connection
import random
import string
from django.conf import settings
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

def generate_strong_password(length=10):
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))



def send_password_reset_email(email1):
    subject = "Your Password Reset OTP"
    new_password = generate_strong_password()
    
    message = f'Your New for password  is: {new_password}\n.'
    email_from = settings.EMAIL_HOST_USER
    
    try:
        user_obj = User.objects.get(email=email1)
        user_obj.set_password(new_password)
        user_obj.save()
        
        send_mail(subject, message, email_from, [email1])
        return True
    except User.DoesNotExist:
        return False

