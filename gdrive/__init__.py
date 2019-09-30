import logging, datetime
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from os import listdir
from os.path import isfile, join

today = datetime.datetime.now()
date = today.strftime('%Y%m%d')
format_string = "%(asctime)s [%(levelname)s] [%(name)s:%(funcName)s]: %(message)s"
formatter = logging.Formatter(format_string)
logging.basicConfig(format=format_string, level=logging.DEBUG)
logger = logging.getLogger(__name__)
ch = logging.FileHandler("log/log.%s" % date)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
logger.addHandler(ch)

class GoogleUtility():
    def __init__(self):
        self.username = '' # Enter user information
        self.googleFolderId = '1NHhbWz36FWEbS4q4xMe3ys8Dsi_J44jE' # Select which folder to use
        self.fileName = ''

    def authenticate(self, fileName):
        self.fileName = fileName
        gauth = GoogleAuth()
        gauth.LocalWebserverAuth()
        if(self.getFiles(gauth)):
            return True
        else:
            logger.error('Google failed to get files.')
            return False

    def getFiles(self, gauth):
        # push to Goole Drive
        if gauth.credentials is None:
            gauth.LocalWebserverAuth()
            logger.error("Google authentication failed, no credentials")
            #gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            logger.info("Google Expired token!")
            gauth.Refresh()
            logger.info("Google Refreshing token")
        else:
            logger.info("Google Reauthorizing credentials...")
            gauth.Authorize()
        # Save credentials
        gauth.SaveCredentialsFile("mycreds.txt")
        drive = GoogleDrive(gauth)
        file_list = drive.ListFile({'q': "'"+self.googleFolderId+"' in parents and trashed=false"}).GetList()
        for file1 in file_list:
            logger.info('Found: %s, id: %s' % (file1['title'], file1['id']))
            if file1['title'] == self.fileName:
                logger.info('Downloading: %s, id: %s' % (file1['title'], file1['id']))
                inFile = drive.CreateFile({'id': file1['id']})
                inFile.GetContentFile('csv/'+file1['title']+'.csv', mimetype='text/csv')
                return True
