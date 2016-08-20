#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import xbmc, xbmcgui, xbmcaddon



__author__ = 'harryberlin'

ADDON = xbmcaddon.Addon()
ADDONNAME = ADDON.getAddonInfo('name')
ADDONID = ADDON.getAddonInfo('id')
ADDONPATH = ADDON.getAddonInfo('path')
ADDONVERSION = ADDON.getAddonInfo('version')

ICON = os.path.join(ADDONPATH, 'icon.png')


def log(message):
    xbmc.log('plugin.script.logmailer: %s' % message, xbmc.LOGNOTICE)


def note(heading, message=None, time=5000):
    xbmcgui.Dialog().notification(heading='%s' % heading, message='%s' % message if message else '', icon=ICON, time=time)
    log('NOTIFICATION: "%s%s"' % (heading, ' - %s' % message if message else ''))


def dialog_ok(label1, label2=None, label3=None):
    log('DIALOG_OK: "%s%s%s"' % (label1, ' - %s' % label2 if label2 else '', ' - %s' % label3 if label3 else ''))
    xbmcgui.Dialog().ok('Log Mailer', label1, label2, label3)


def get_addon_setting(id):
    setting = xbmcaddon.Addon().getSetting(id)
    if setting.upper() == 'TRUE': return True
    if setting.upper() == 'FALSE': return False
    return '%s' % setting


def open_settings():
    if xbmcgui.getCurrentWindowDialogId() == 10140:
        xbmc.executeJSONRPC('{ "jsonrpc": "2.0", "method": "Input.Back", "id": 1 }')
    else:
        xbmcaddon.Addon().openSettings()


def send_logfile():

    progress = xbmcgui.DialogProgress()
    progress.create('Log Mailer','Load Settings...')

    import time
    import smtplib
    import zipfile
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email.mime.multipart import MIMEMultipart
    from email import encoders

    # eMail-Adressen (Sender/Empfaenger)
    mailSender = get_addon_setting('mail_adress')
    if mailSender == '':
        dialog_ok('Setting Error', 'E-Mail Adress is missing')
        return
    log('Sender: %s' % mailSender)

    log_mode = get_addon_setting('mail_log_mode')
    if log_mode == '0':
        Hostname = "BMWRaspControl"
        mailReceiver = 'net@net.net'
        full_file_path = ''
    elif log_mode == '1':
        Hostname = "IBusCommunicator"
        mailReceiver = 'ZGVidWcuaWJ1c2NvbW11bmljYXRvckBnbXguZGU='.decode('base64', 'strict')
        full_file_path = '/home/osmc/.kodi/temp/kodi.log'
    else:
        return
    log('Receiver: %s' % mailReceiver)

    msg = MIMEMultipart()
    msg['Subject'] = "%s LogFile-Export" % Hostname
    msg['From'] = mailSender
    msg['To'] = mailReceiver

    smtpHost = get_addon_setting('mail_out_server')
    if smtpHost == '':
        dialog_ok('Setting Error', 'SMTP Server is missing')
        return
    log('SMTP Host: %s' % smtpHost)

    smtpSecureMode = get_addon_setting('mail_out_secure')
    if smtpSecureMode == '1':
        smtpPort = int(get_addon_setting('mail_out_ssl_port'))
    else:
        smtpPort = int(get_addon_setting('mail_out_port'))
    log('SMTP Port: %s' % smtpPort)

    progress.update(10,'Connecting Server...')

    log('SMTP Server connecting...')
    log('SMTP Host: %s, Port: %s, SSL: %s' % (smtpHost, smtpPort, 'Yes' if smtpSecureMode == '1' else 'No'))
    try:
        if smtpSecureMode == '1':
            server = smtplib.SMTP_SSL(timeout=3)
            log('SSL Connection')
        else:
            server = smtplib.SMTP(timeout=3)
        server.connect(smtpHost, smtpPort)

    except smtplib.socket.error:
        dialog_ok('Connection Error','Host: %s, Port: %s, SSL: %s' % (smtpHost, smtpPort, get_addon_setting('mail_ssl')))
        return

    server.ehlo_or_helo_if_needed()
    if smtpSecureMode == '2':
        server.starttls()  # If TLS authentication is not required set a hash at the beginning of this line
        log('STARTTLS is True')

    server.ehlo_or_helo_if_needed()

    # SMTP-Ausgangsserver (Sender)
    smtpUser = get_addon_setting('mail_out_user')
    if smtpUser == '':
        dialog_ok('Setting Error', 'Login Name is missing')
        return
    log('SMTP User: %s' % smtpUser)

    smtpPassword = get_addon_setting('mail_out_password')
    if smtpPassword == '':
        log('SMTP Password not stored. Ask User for Input')
        password = xbmcgui.Dialog().input('%s password:' % smtpUser, option=xbmcgui.ALPHANUM_HIDE_INPUT)
        if password != '':
            smtpPassword = password
        else:
            dialog_ok('no password entered')
            return

    server.login(smtpUser, smtpPassword)
    log('SMTP Server connected')
    progress.update(30, 'Server connected')

    progress.update(50, 'Prepare E-Mail...')
    ###############################################################################
    # Time/Date Recording for Filename
    fndate = "%04i%02i%02i" % (int(time.localtime()[0]), int(time.localtime()[1]), int(time.localtime()[2]))
    fntime = "%02i%02i%02i" % (int(time.localtime()[3]), int(time.localtime()[4]), int(time.localtime()[5]))

    MailContent = "Die exportierten LogFiles befinden sich im Anhang dieser eMail. " + "\n" + "\n" + "__________________________" + "\n" + "Es handelt sich hierbei um eine automatisch generierte E-Mail, die von Ihrem Raspberry Pi (" + Hostname + ") gesendet worden ist."
    msg.attach(MIMEText(MailContent, 'plain'))

    filename = "Log-Export_" + Hostname + "_" + fndate + "_" + fntime + ".zip"

    progress.update(60, 'Prepare E-Mail Attachments...')
    log('create zip file')
    zip = zipfile.ZipFile(os.path.join(ADDONPATH, filename), 'w', zipfile.ZIP_DEFLATED)
    zip.write(full_file_path,os.path.split(full_file_path)[1])
    zip.close()


    log('open file for mail')
    attachment = open(os.path.join(ADDONPATH, filename), "rb")

    part = MIMEBase('application', 'octet-stream')
    log('read file %s' % filename)
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    msg.attach(part)
    #try:
    progress.update(75, 'Send E-Mail...')
    log('send mail')
    server.sendmail(mailSender, mailReceiver, msg.as_string())
    note('E-Mail sent successfull')
    #except:
    #    dialog_ok('Error: E-Mail not sent')
    server.quit()
    progress.update(99, 'E-Mail sent')

    log('delete zip file')
    progress.update(100, 'Delete Tempfile')
    time.sleep(1)
    if os.path.isfile(os.path.join(ADDONPATH, filename)):
        os.remove(os.path.join(ADDONPATH, filename))

    progress.close()


def main():
    count = len(sys.argv) - 1
    if count > 0:
        given_args = sys.argv[1].split(';')
        if str(given_args[0]) == "send_logfile":
            send_logfile()
        elif str(given_args[0]) == "settings":
            open_settings()
        else:
            print ('Unknown Arguments given!')

    else:
        open_settings()


if __name__ == '__main__':
    #print 'net@net.net'.encode('base64', 'strict')
    #print 'bmV0QG5ldC5uZXQ='.decode('base64', 'strict')
    main()
