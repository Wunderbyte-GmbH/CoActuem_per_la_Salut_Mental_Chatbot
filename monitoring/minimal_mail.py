import smtplib
import keyring
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders

def add_inline_img(html_before, image_path):
    image_id = image_path
    image_html = "<p><img src='cid:image1' alt='monitoring inline img'  width='600'> </p>"
    return html_before + image_html
    
def set_font(html):
    """ coorporate design CoAct: Glacial Indifference"""    
    return "<font face='Glacial Indifference' size='3.5' color='black'>"+ html +"</font>"

def send_mail(subject, mail_body, images_in_mail_body=[], attachment_path_list=[]):
    # set mail parameters
    MY_ADDRESS   = 'mymail@ub.edu'
    PASSWORD     = keyring.get_password("mail", "fpeter")
    mail         = "mail@ub.edu, of@ub.edu, my@ub.edu, team@ub.edu"
    subject      = subject#"CoAct chatbot: daily mail monitoring"
    message_text = mail_body#"Esto es el resumen de hoy: "

    # set up the SMTP server
    s = smtplib.SMTP(host='smtp-mail.outlook.com', port=587)
    s.starttls()
    s.login(MY_ADDRESS, PASSWORD)

    # create a message
    msg = MIMEMultipart()

    # setup the parameters of the message
    msg['From']   = MY_ADDRESS
    msg['To']     = mail   
    msg['Subject']= subject

    # add the message body
    message = set_font(message_text) 
    for image_path in images_in_mail_body:
        message = add_inline_img(message, image_path)
    body = MIMEText(message.encode('utf-8'), 'html', 'utf-8')
    msg.attach(body)
    
    for image_path in images_in_mail_body:
        # add mail footer image
        fp = open(image_path, 'rb')
        msgImage = MIMEImage(fp.read())
        fp.close()

        # Define the image's ID as referenced above
        image_id = "<"+image_path+">"
        msgImage.add_header('Content-ID', 'image_id')
        msg.attach(msgImage)
    
    for each_file_path in attachment_path_list:
        file_name=each_file_path.split("/")[-1]
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(each_file_path, "rb").read())
        
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment', filename=file_name)
        msg.attach(part)

    # send
    s.send_message(msg)

    # Terminate the SMTP session and close the connection
    s.quit()
