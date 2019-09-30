import json, requests, time, urllib3, datetime, logging
urllib3.disable_warnings()

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

class Echosign():
    def __init__(self, token):
        self.url = 'https://api.na1.echosign.com/api/rest/v6/'
        self.agreementId = ''
        self.xapiuser = 'email:echosign@docircle.com'
        self.authorization = 'Bearer '+token
        self.etag = ''
        self.documentId = '' # Select document template
        self.documentName = 'Customer Invoice - '
        self.headers = {'Content-Type':'application/json','x-api-user':self.xapiuser,'Authorization':self.authorization,'If-Match':self.etag}

    def refreshToken():
        # Insert echosign token and client information
        CONST_CLIENTID = ''
        CONST_CLIENTSECRET = ''
        refreshToken = ''
        url = 'https://secure.na1.echosign.com/oauth/refresh'
        header = {'Content-Type':'application/x-www-form-urlencoded'}
        data = {'grant_type':'refresh_token', 'client_secret':CONST_CLIENTSECRET, 'client_id':CONST_CLIENTID,'refresh_token':refreshToken}
        try:
            response = requests.post(url, data, headers=header)
            if response.status_code == requests.codes.ok:
                logger.info("Echosign Token Refreshed: "+response.json()['access_token'])
                return(response.json()['access_token'])
            else:
                logger.debug(response.raise_for_status())
                return(False)
        except Exception as e:
            logger.error('Echosign Refresh Token - EXCEPTION: '+str(e))

    # Create agreement, set status of agreement with "state"
    def putAgreement(self, recipientEmail, username, state):
        #recipientEmail = 'vu.kevin00@gmail.com'
        jsonData = {"fileInfos":[{"libraryDocumentId":self.documentId}],"name":self.documentName+username,"participantSetsInfo":[{"memberInfos":[{"email":recipientEmail}],"order":1,"role":"SIGNER"}],"signatureType":"ESIGN","state":state}
        try:
            response = requests.post(self.url+'agreements', data=json.dumps(jsonData), headers=self.headers)
            if response.status_code == requests.codes.created:
                self.agreementId = response.json()['id']
                logger.info("Sending Draft Agreement - ID: "+self.agreementId)
                return(True)
            else:
                logger.error('Draft Agremeent failed: '+response.raise_for_status())
                return(False)
        except Exception as e:
            logger.error('Draft agreement EXCEPTION: '+str(e))

    def putState(self, state):
        try:
            #self.etag = ''
            jsonData = {"state":state}
            del self.headers['If-Match']
            response = requests.request('PUT', self.url+'agreements/'+self.agreementId+'/state', json=jsonData, headers=self.headers, verify=False)
            if response.status_code == requests.codes.no_content:
                logger.info("Invoice Sent!")
            else:
                logger.debug('Change State failed: '+response.raise_for_status())
                return(False)
        except Exception as e:
            logger.error('Change State EXCEPTION: '+str(e))

    # This function is used to get the ETag in the header.
    def getMergeInfo(self):
        try:
            response = requests.get(self.url+'agreements/'+self.agreementId+'/formFields/mergeInfo', headers=self.headers)
            #print(response.text)
            if response.status_code == requests.codes.ok:
                self.etag = response.headers['ETag']
                logger.info("Get Merge Info - ETag: "+self.etag)
                self.headers = {'Content-Type':'application/json','x-api-user':self.xapiuser,'Authorization':self.authorization,'If-Match':self.etag}
                return(True)
            else:
                logger.debug('Change State failed: '+response.raise_for_status())
                return(False)
        except Exception as e:
            logger.error('Get Merge Info EXCEPTION: '+str(e))

    def putMergeInfo(self, inData):
        # TO DO, multiple PONUMBER, SERVICE, AMOUNT
        today = datetime.date.today().strftime('%m/%d/%Y')
        terms1 = 'Due Upon Receipt'
        subTotal = ''
        jsonData = {"fieldMergeInfos":[{"defaultValue":inData['to'],"fieldName":"to"},{"defaultValue":inData['username'],"fieldName":"username"},{"defaultValue":today,"fieldName":"date"},{"defaultValue":inData['customerName'],"fieldName":"customerName"},{"defaultValue":inData['customerEmail'],"fieldName":"customerEmail"},{"defaultValue":inData['docircleName'],"fieldName":"docircleName"},{"defaultValue":inData['docircleTitle'],"fieldName":"docircleTitle"},{"defaultValue":inData['docircleEmail'],"fieldName":"docircleEmail"},{"defaultValue":terms1,"fieldName":"terms1"},{"defaultValue":inData['subTotal'],"fieldName":"subtotal"},{"defaultValue":inData['subTotal'],"fieldName":"total"}]}

        # Adding multiple services
        for i in range(1, 9):
            if 'service'+str(i) in inData:
                inService = 'service'+str(i)
                inAmount = 'amount'+str(i)
                jsonData['fieldMergeInfos'].append({"defaultValue":inData[inService],"fieldName":inService})
                jsonData['fieldMergeInfos'].append({"defaultValue":inData[inAmount],"fieldName":inAmount})
                subTotal += inData[inAmount]
            else:
                break
        try:
            #print('-----------------')
            #print("Put merge info")
            #print(self.headers)
            response = requests.request('PUT', self.url+'agreements/'+self.agreementId+'/formFields/mergeInfo', json=jsonData, headers=self.headers, verify=False)
            if response.status_code == requests.codes.no_content:
                return(True)
            else:
                logger.debug('Put Merg Info failed: '+response.raise_for_status())
                return(False)
        except Exception as e:
            logger.error('Put Merge Info EXCEPTION: '+str(e))

    # NOT IN USE
    def getAgreement(self):
        try:
            response = requests.get(self.url+'agreements/'+self.agreementId, headers=self.headers)
            if response.status_code == requests.codes.created:
                self.etag = response.headers['ETag']
                print('-----------------')
                print("Get Agreement - Etag: "+self.etag)
                return(True)
            else:
                response.raise_for_status()
        except Exception as e:
            print(e)

    # NOT IN USE
    def getFormFields(self):
        try:
            self.etag = ''
            response = requests.get(self.url+'agreements/'+self.agreementId+'/formFields', headers=self.headers)
            #print(response.text)
            if response.status_code == requests.codes.ok:
                print('-----------------')
                print(response.headers)
                self.etag = response.headers['ETag']
                print("Get Form Fields - ETag: "+self.etag)
                self.headers = {'Content-Type':'application/json','x-api-user':self.xapiuser,'Authorization':self.authorization,'If-Match':self.etag}
                return(True, response.json())
            else:
                response.raise_for_status()
        except Exception as e:
            print(e)

    # NOT IN USE
    def putFormFields(self, jsonData, inData):
        #print(jsonData['fields'][0])
        # key = documentKey
        for item in jsonData['fields']:
            if item['name'] in inData:
                item['defaultValue'] = inData[item['name']]
                print(item['defaultValue'])
                print(inData[item['name']])
        print('-----')
        print(jsonData)
        #try:
        #    print('-----------------')
        #    print("Put Form Fields")
        #    print(self.headers)
        #    response = requests.request('PUT', self.url+'agreements/'+self.agreementId+'/formFields', json=jsonData, headers=self.headers, verify=False)
        #    if response.status_code == requests.codes.no_content:
        #        return(True)
        #    else:
        #        response.raise_for_status()
        #except Exception as e:
        #    print(e)
