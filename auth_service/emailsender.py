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
        message['Subject'] = 'Подтверждение email — РСК'

        confirmation_url = f"{settings.URL_FOR_TOKEN}/confirm-email?token={token}"
        
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
            }}
            .lead {{
                margin: 0 0 18px 0;
                color: #0b1220;
                font-size: 16px;
            }}
            .button-wrap {{
                text-align: center;
                padding: 10px 0 20px 0;
            }}
            .btn {{
                display: inline-block;
                text-decoration: none;
                padding: 12px 22px;
                border-radius: 10px;
                background: linear-gradient(90deg, #3a6bff, #6366f1);
                color: #ffffff;
                font-weight: 600;
                font-size: 15px;
            }}
            .muted {{
                color: #94a3b8;
                font-size: 13px;
                padding-top: 6px;
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
                .btn {{
                    padding: 12px 18px;
                    font-size: 15px;
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
                                <h1>Подтверждение email</h1>
                            </td>
                        </tr>

                        <tr>
                            <td class="content">
                                <p class="lead">Спасибо за регистрацию на платформе РСК!</p>

                                <p>Мы будем оповещать вас о важных обновлениях платформы и о конкурсе на эту почту. Пожалуйста, подтвердите адрес электронной почты, чтобы завершить регистрацию и получить все уведомления.</p>

                                <div class="button-wrap" role="presentation">
                                    <a href="{confirmation_url}" class="btn" target="_blank" rel="noopener noreferrer">Подтвердить почту</a>
                                </div>

                                <p class="muted small">Если кнопка не работает, скопируйте и вставьте эту ссылку в адресную строку браузера:</p>
                                <p class="small" style="word-break: break-all">
                                    <a href="{confirmation_url}" target="_blank" style="color: #3a6bff; text-decoration: none">{confirmation_url}</a>
                                </p>

                                <hr style="border: none; border-top: 1px solid #eef2f7; margin: 20px 0" />

                                <p class="small">Если вы не регистрировались на платформе РСК, проигнорируйте это письмо — никакие действия не будут выполнены.</p>
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
        # Не поднимаем исключение, чтобы не ломать регистрацию
        # Просто логируем ошибку
