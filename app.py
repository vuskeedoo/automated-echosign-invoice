import requests, json, datetime, csv, time, logging
from dateutil.relativedelta import relativedelta
from echosign import Echosign
from gdrive import GoogleUtility

# Logger settings
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

# Pause time after refresh token
CONST_SLEEP = 1.5
# Row counter to use for Adobe API.
CONST_ROW = 0
dataRow = []

# Find current month + 3 months
current_month = datetime.date.today() + relativedelta(months=3)
searchMonth = (current_month.strftime('%B%Y'))
#searchMonth = 'November2019'

def runGoogle():
    # Download file from Google Drive
    gdrive = GoogleUtility()
    if(gdrive.authenticate(searchMonth)):
        logger.info('Downloading file from drive: '+searchMonth)
    else:
        logger.error('Downloading failed!')

def runCSV():
    # Read file. Create dictionary with each row. Append to 'dataRow'
    with open('csv/'+searchMonth+'.csv', mode='r') as csv_file:
        today = datetime.date.today().strftime('%m/%d/%Y')
        csv_reader = csv.DictReader(csv_file)
        row_count = 0
        for row in csv_reader:
            inData = {}
            if(row['to'] is ''):
                break
            inData['to'] = row['to']
            inData['username'] = row['username']
            inData['date'] = today
            #inData['poNumber1'] = row['poNumber1']
            inData['customerName'] = row['customerName']
            #inData['customerTitle'] = row['customerTitle']
            inData['customerEmail'] = row['customerEmail']
            inData['docircleName'] = row['docircleName']
            inData['docircleTitle'] = row['docircleTitle']
            inData['docircleEmail'] = row['docircleEmail']
            #inData['terms1'] = row['terms1']
            inData['subTotal'] = row['subTotal']
            # Adding multiple services
            for i in range(1, 9):
                if 'service'+str(i) in row:
                    if row['service'+str(i)] != '':
                        inData['service'+str(i)] = row['service'+str(i)]
                        inData['amount'+str(i)] = row['amount'+str(i)]
                    else:
                        break
                else:
                    break
            dataRow.append(inData)
            row_count += 1
            logger.info('Row #'+str(row_count)+': '+str(inData))
        CONST_ROW = row_count

def runEcho():
    # Echosign work flow
    token = Echosign.refreshToken()
    esign = Echosign(token)
    time.sleep(CONST_SLEEP)
    count = 0
    # Cycle through dataRow and create Echosign agreements.
    for dRow in dataRow:
        count += 1
        if dRow['to'] is not '':
            logger.info('Sending agreement #'+str(count)+ ' to: '+dRow['to'])
            logger.debug(dRow)
            if(esign.putAgreement(dRow['to'], dRow['username'], 'DRAFT')):
                if(esign.getMergeInfo()):
                    if(esign.putMergeInfo(dRow)):
                        esign.putState("IN_PROCESS")
                    else:
                        logger.error('PUT Merge Info failed to: '+dRow['to'])
                else:
                    logger.error('GET Merge Info failed to: '+dRow['to'])
            else:
                logger.error('Sending agreement failed to: '+dRow['to'])
        else:
            break

runGoogle()
runCSV()
runEcho()
