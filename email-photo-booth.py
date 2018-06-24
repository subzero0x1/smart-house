#!/usr/bin/env python


import sys
import logging
import argparse


def check_photo_request(hostname, username, password, boss):
    from imapclient import IMAPClient
    import email
    from email.utils import parseaddr

    server = IMAPClient(hostname, use_uid=True, ssl=True)
    server.login(username, password)
    select_info = server.select_folder('Inbox')
    msg_count = select_info[b'EXISTS']
    if msg_count == 0:
        return False
    command_photo = False
    messages = server.search()
    for msgid, data in server.fetch(messages, [b'RFC822']).items():
        msg = email.message_from_bytes(data[b'RFC822'])
        subject = str(msg['Subject'])
        mfrom = str(parseaddr(msg['From'])[1])
        if 'photo' == subject.strip().lower() and boss == mfrom.strip().lower():
            command_photo = True
            break
    server.delete_messages(messages, silent=True)
    server.expunge(messages)
    server.logout()
    return command_photo


def take_picture(image_file):
   from picamera import PiCamera
   cam = PiCamera()
   cam.capture(image_file)


def read_image_data(file_path):
    return open(file_path, 'rb').read()


def send_picture(image_data, image_file, adr_from, adr_to, smtphost, username, password):
    import os
    import datetime
    from smtplib import SMTP_SSL as SMTP
    from email.mime.image import MIMEImage
    from email.mime.multipart import MIMEMultipart

    msg = MIMEMultipart()
    image = MIMEImage(image_data, name=os.path.basename(image_file))
    msg.attach(image)
    msg['Subject'] = 'Photo from Assistant at ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg['From'] = adr_from
    msg['To'] = adr_to
    sender = SMTP(smtphost)
    sender.login(username, password)
    sender.send_message(msg)
    sender.quit()


parser = argparse.ArgumentParser(description='E-mail Photo Booth')
parser.add_argument('--imagefile', nargs=1, type=str, required=True, help='file to store photo to')
parser.add_argument('--imaphost', nargs=1, type=str, required=True, help='IMAP host name')
parser.add_argument('--smtphost', nargs=1, type=str, required=True, help='SMTP host name')
parser.add_argument('--username', nargs=1, type=str, required=True, help='username')
parser.add_argument('--password', nargs=1, type=str, required=True, help='password')
parser.add_argument('--boss', nargs=1, type=str, required=True, help='Boss E-mail')
parser.add_argument('--assistant', nargs=1, type=str, required=True, help='Assistant E-mail')
args = parser.parse_args()
imagefile = args.imagefile[0]
imaphost = args.imaphost[0]
smtphost = args.smtphost[0]
username = args.username[0]
password = args.password[0]
boss = args.boss[0]
assistant = args.assistant[0]

logging.basicConfig(format='%(asctime)-15s %(message)s')
logger = logging.getLogger('email-photo-booth')
logger.setLevel(level=logging.DEBUG)
logger.debug('email-photo-booth started')

try:
    if check_photo_request(imaphost, username, password, boss):
        logger.debug('trying to take photo')
        take_picture(imagefile)
        logger.debug('photo taken to ' + imagefile)
        logger.debug('trying to read photo from ' + imagefile)
        image_data = read_image_data(imagefile)
        logger.debug('photo red')
        logger.debug('trying to send photo to ' + boss + ' from ' + assistant + ' via ' + smtphost)
        send_picture(image_data, imagefile, assistant, boss, smtphost, username, password)
        logger.debug('photo has been sent')
    else:
        logger.debug('no photo requests')
except:
    print("Unexpected error: ", sys.exc_info())

logger.debug('email-photo-booth finished')
