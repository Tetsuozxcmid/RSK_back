import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import HTTPException
from config import settings

import logging

logger = logging.getLogger(__name__)

async def send_ok_email(recipient_email: str):
    try:
        message = MIMEMultipart()
        message['From'] = settings.SENDER_EMAIL
        message['To'] = recipient_email
        message['Subject'] = 'Решение о курсе — РСК'

        confirmation_message = f"Привет твое решение было одобрено администрацией,можешь взять еще задач!"
        
        html_body = f"""
<!DOCTYPE html>
<html lang="ru">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>Подтверждение email — РСК</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #f4f6fb;
                font-family: "Helvetica Neue", Arial, sans-serif;
                -webkit-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
            }}
            .wrapper {{
                width: 100%;
                table-layout: fixed;
                background-color: #f4f6fb;
                padding: 24px 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 6px 18px rgba(20, 30, 60, 0.08);
            }}
            .header {{
                padding: 28px 30px 0 30px;
                text-align: center;
            }}
            .logo {{
                max-width: 120px;
                display: inline-block;
                margin-bottom: 10px;
            }}
            h1 {{
                margin: 8px 0 0 0;
                font-size: 22px;
                color: #0f1724;
            }}
            .content {{
                padding: 22px 30px 32px 30px;
                color: #475569;
                line-height: 1.45;
                font-size: 15px;
                text-align: center;
            }}
            .lead {{
                margin: 0 0 18px 0;
                color: #0b1220;
                font-size: 16px;
                font-weight: bold;
            }}
            .message-box {{
                background-color: #f8fafc;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                border-left: 4px solid #3a6bff;
            }}
            .footer {{
                padding: 18px 30px 28px 30px;
                text-align: center;
                color: #94a3b8;
                font-size: 13px;
            }}
            .small {{
                font-size: 12px;
                color: #9aa6bb;
            }}
            @media (max-width: 420px) {{
                .container {{
                    margin: 0 16px;
                    border-radius: 10px;
                }}
                h1 {{
                    font-size: 20px;
                }}
                .content {{
                    padding: 18px;
                }}
            }}
        </style>
    </head>
    <body>
        <table class="wrapper" cellpadding="0" cellspacing="0" role="presentation" width="100%">
            <tr>
                <td align="center">
                    <table class="container" cellpadding="0" cellspacing="0" role="presentation" width="100%">
                        <tr>
                            <td class="header">
                                <img class="logo" src="https://rosdk.ru/images/logo.svg" alt="RSK" />
                                <h1>Уведомление — РСК</h1>
                            </td>
                        </tr>

                        <tr>
                            <td class="content">
                                <p class="lead">Ваш курс был подтвержден!</p>
                                
                                <div class="message-box">
                                    <p style="margin: 0; font-size: 16px; color: #0f1724;">{confirmation_message}</p>
                                </div>

                                <p>Пожалуйста, проверьте информацию в вашем личном кабинете на платформе РСК.</p>

                                <hr style="border: none; border-top: 1px solid #eef2f7; margin: 20px 0" />

                                <p class="small">С уважением,<br>Команда платформы РСК</p>
                            </td>
                        </tr>

                        <tr>
                            <td class="footer">
                                <div class="small">
                                    Платформа РСК · <span style="white-space: nowrap">© 2024</span>
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
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


async def send_bad_email(recipient_email: str):
    try:
        message = MIMEMultipart()
        message['From'] = settings.SENDER_EMAIL
        message['To'] = recipient_email
        message['Subject'] = 'Решение о курсе  — РСК'

        confirmation_message = f"Привет твое решение было отклонено администрацией,можешь попробовать еще раз!"
        
        html_body = f"""
<!DOCTYPE html>
<html lang="ru">
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1" />
        <title>Подтверждение email — РСК</title>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: #f4f6fb;
                font-family: "Helvetica Neue", Arial, sans-serif;
                -webkit-text-size-adjust: 100%;
                -ms-text-size-adjust: 100%;
            }}
            .wrapper {{
                width: 100%;
                table-layout: fixed;
                background-color: #f4f6fb;
                padding: 24px 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background: #ffffff;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 6px 18px rgba(20, 30, 60, 0.08);
            }}
            .header {{
                padding: 28px 30px 0 30px;
                text-align: center;
            }}
            .logo {{
                max-width: 120px;
                display: inline-block;
                margin-bottom: 10px;
            }}
            h1 {{
                margin: 8px 0 0 0;
                font-size: 22px;
                color: #0f1724;
            }}
            .content {{
                padding: 22px 30px 32px 30px;
                color: #475569;
                line-height: 1.45;
                font-size: 15px;
                text-align: center;
            }}
            .lead {{
                margin: 0 0 18px 0;
                color: #0b1220;
                font-size: 16px;
                font-weight: bold;
            }}
            .message-box {{
                background-color: #f8fafc;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                border-left: 4px solid #3a6bff;
            }}
            .footer {{
                padding: 18px 30px 28px 30px;
                text-align: center;
                color: #94a3b8;
                font-size: 13px;
            }}
            .small {{
                font-size: 12px;
                color: #9aa6bb;
            }}
            @media (max-width: 420px) {{
                .container {{
                    margin: 0 16px;
                    border-radius: 10px;
                }}
                h1 {{
                    font-size: 20px;
                }}
                .content {{
                    padding: 18px;
                }}
            }}
        </style>
    </head>
    <body>
        <table class="wrapper" cellpadding="0" cellspacing="0" role="presentation" width="100%">
            <tr>
                <td align="center">
                    <table class="container" cellpadding="0" cellspacing="0" role="presentation" width="100%">
                        <tr>
                            <td class="header">
                                <img class="logo" src="https://rosdk.ru/images/logo.svg" alt="RSK" />
                                <h1>Уведомление — РСК</h1>
                            </td>
                        </tr>

                        <tr>
                            <td class="content">
                                <p class="lead">Ваш курс был подтвержден!</p>
                                
                                <div class="message-box">
                                    <p style="margin: 0; font-size: 16px; color: #0f1724;">{confirmation_message}</p>
                                </div>

                                <p>Пожалуйста, проверьте информацию в вашем личном кабинете на платформе РСК.</p>

                                <hr style="border: none; border-top: 1px solid #eef2f7; margin: 20px 0" />

                                <p class="small">С уважением,<br>Команда платформы РСК</p>
                            </td>
                        </tr>

                        <tr>
                            <td class="footer">
                                <div class="small">
                                    Платформа РСК · <span style="white-space: nowrap">© 2024</span>
                                </div>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
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
        