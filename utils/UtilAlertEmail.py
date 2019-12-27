import smtplib
import json
import os

from string import Template
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
CONFIG = json.loads(open(os.path.join(ROOT_DIR, '../config/EmailConfig.json')).read())

EMAIL_ADDRESS = CONFIG['CURW_EMAIL_ADDRESS']
PASSWORD = CONFIG['CURW_EMAIL_PASSWORD']
HOST = CONFIG['CURW_EMAIL_HOST']
PORT = CONFIG['CURW_EMAIL_PORT']

def get_contacts(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.
    """

    names = []
    emails = []
    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            names.append(a_contact.split()[0])
            emails.append(a_contact.split()[1])
    return names, emails


def read_template(filename):
    """
    Returns a Template object comprising the contents of the
    file specified by filename.
    """

    with open(filename, 'r') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)


def send_email(subject, station_name, variable_type, recorded_value, recorded_time):

    message_template = read_template('email_content.txt')

    # set up the SMTP server
    server = smtplib.SMTP(host=HOST, port=587)
    server.starttls()
    server.login(EMAIL_ADDRESS, PASSWORD)

    # For each contact, send the email:
    names = ['Shasini Umesha', 'Muditha Danthanarayana']
    emails = ['shasiniumesha274@gmail.com', 'muditha.danta@eng.pdn.ac.lk']

    for name, email in zip(names, emails):
        msg = MIMEMultipart()

        message = message_template.substitute(Station=station_name.title(), Variable=variable_type.title(),
                                              Value=recorded_value.title(), Time=recorded_time.title())

        # setup the parameters of the message
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = email
        msg['Subject'] = subject

        # add in the message body
        msg.attach(MIMEText(message, 'plain'))

        # send the message via the server set up earlier.
        server.send_message(msg, msg['From'], msg['To'])
        del msg


    # Terminate the SMTP session and close the connection
    server.quit()

