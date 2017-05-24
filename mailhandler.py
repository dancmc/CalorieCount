from app import app, mail
from flask_mail import Mail, Message
from flask import render_template
from threading import Thread




def send_email(sender, to, subject=None, body=None, template=None):

    def send_async_email(msg):
        with app.app_context():
            mail.send(msg)

    msg = Message(subject,
                  sender=sender,
                  recipients=to)
    if body:
        msg.body = body
    elif template:
        msg.html = render_template('/emails'+template)

    t = Thread(target=send_async_email, args=[msg])
    t.start()
    return t