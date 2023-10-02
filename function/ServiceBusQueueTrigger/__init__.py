import logging
import azure.functions as func
import psycopg2
import os
from datetime import datetime
from sendgrid import SendGridAPIClient, Email, To, Content
from sendgrid.helpers.mail import Mail, HtmlContent
import smtplib
from email.mime.text import MIMEText

def main(msg: func.ServiceBusMessage):

    notification_id = int(msg.get_body().decode('utf-8'))
    logging.info('Python ServiceBus queue trigger processed message: %s',notification_id)
    print(notification_id)

    conn = psycopg2.connect(user="mennt1udacity@techconf-mennt1",
                                    password="UdacityMenNT1@1992",
                                    host="techconf-mennt1.postgres.database.azure.com",
                                    port="5432",
                                    database="techconfdb")
    cursor = conn.cursor()

    try:
        # Get notification message and subject from database using the notification_id
        notification_query = '''SELECT subject, message 
                                FROM notification
                                WHERE id = %s;'''
        cursor.execute(notification_query, (notification_id,))

        # Get attendees email and name
        notification = cursor.fetchone()
        subject = notification[0]
        message = notification[1]

        # Loop through each attendee and send an email with a personalized subject
        attendees_query = 'SELECT first_name, email FROM attendee;'
        cursor.execute(attendees_query)
        attendees = cursor.fetchall() 
        for attendee in attendees:
            first_name = attendee[0]
            email = attendee[1]
            custom_subject = '{}: {}'.format(first_name, subject)
            send_email(email, custom_subject, message)

        # Update the notification table by setting the completed date and updating the status with the total number of attendees notified
        completed_date = datetime.utcnow()
        status = 'Notified {} attendees'.format(len(attendees))
        
        notification_update_query = '''UPDATE notification 
                                SET completed_date = %s, status = %s 
                                WHERE id = %s;'''
        
        cursor.execute(notification_update_query, (completed_date, status, notification_id))
        conn.commit()

    except (Exception, psycopg2.DatabaseError) as error:
        logging.error(error)
    finally:
        if conn:
            cursor.close()
            conn.close()
            print("PostgreSQL connection is closed")

def send_email(email, subject, body):
    # message = Mail(
    #     # from_email=os.environ.get('ADMIN_EMAIL_ADDRESS'),
    #     from_email = "nguyentrungmen@gmail.com",
    #     to_emails=email,
    #     subject=subject,
    #     plain_text_content=body)

    # sg = SendGridAPIClient("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")
    # sg.send(message)

        from_email=os.environ.get('ADMIN_EMAIL_ADDRESS'),
        password=os.environ.get('ADMIN_EMAIL_PASSWORD'),
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = ', '.join(email)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(from_email, password)
            smtp_server.sendmail(from_email, email, msg.as_string())
        print("Message sent!")
        