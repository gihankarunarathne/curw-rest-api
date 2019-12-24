import smtplib

def send_email(subject, msg):
    SENDER_EMAIL_ADDRESS = "curwalerts@gmail.com"
    RECEIVER_EMAIL_ADDRESS = "shasiniumesha274@gmail.com"
    PASSWORD = "curwalerts@data"

    try:
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(SENDER_EMAIL_ADDRESS, PASSWORD)
        message = 'Subject: {}\n\n{}'.format(subject, msg)
        server.sendmail(SENDER_EMAIL_ADDRESS, RECEIVER_EMAIL_ADDRESS, message)
        server.quit()
        print("Success: Email sent!")
    except:
        print("Email failed to send.")


