import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from config import settings

import logging

logger = logging.getLogger(__name__)

async def send_confirmation_email(recipient_email: str, token: str):
    try:
        message = MIMEMultipart()
        message['From'] = settings.SENDER_EMAIL
        message['To'] = recipient_email
        message['Subject'] = 'Email Confirmation'

        confirmation_url = f"{settings.URL_FOR_TOKEN}{token}"
        
        
        html_body = f"""
        <html>
        <body>
            <h2>Email Confirmation</h2>
            <p>Please click the following link to confirm your email:</p>
            <a href="{confirmation_url}">Confirm Email</a>
            
        </body>
        </html>
        """
        
        message.attach(MIMEText(html_body, 'html'))

        
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()  
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SENDER_EMAIL, recipient_email, message.as_string())
            
        logger.info(f"Confirmation email sent to {recipient_email}")
            
    except Exception as e:
        
        logger.error(f"Failed to send confirmation email to {recipient_email}: {str(e)}")
        

