import requests
import argparse
import xmltodict
import json
import glob
import errno
import sys

from os.path import isfile
from requests import Session
from requests.auth import HTTPBasicAuth
from lxml import etree
from zeep import Client, Settings, Plugin
from zeep.transports import Transport
from zeep.cache import SqliteCache
from zeep.plugins import HistoryPlugin
from zeep.exceptions import Fault

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

# This class lets you view the incoming and outgoing http headers and/or XML
class MyLoggingPlugin(Plugin):

    def ingress(self, envelope, http_headers, operation):
#        print(etree.tostring(envelope, pretty_print=True))
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
#        print(etree.tostring(envelope, pretty_print=True))
        return envelope, http_headers

with open('serverparams.json') as json_file:
    data = json.load(json_file)
    for p in data['params']:
        CUCM = p['CUCM']
        USERNAME = p['USERNAME']
        PASSWD = p['PASSWD']
        PUSERNAME = p['PUSERNAME']
        PPASSWD = p['PPASSWD']

CUCM_URL = 'https://' + CUCM + ':8443/realtimeservice2/services/RISService'
WSDL_URL = 'https://' + CUCM + ':8443/realtimeservice2/services/RISService?wsdl'

AXL_WSDL_URL = 'AXLAPI.wsdl'
AXL_CUCM_URL = 'https://' + CUCM + ':8443/axl/'

# This is where the meat of the application starts
# The first step is to create a SOAP client session

session = Session()

# history shows http_headers
history = HistoryPlugin()

# We avoid certificate verification by default, but you can uncomment and set
# your certificate here, and comment out the False setting

#session.verify = CERT
session.verify = False
session.auth = HTTPBasicAuth(USERNAME, PASSWD)

transport = Transport(session=session, timeout=10, cache=SqliteCache())

# strict=False is not always necessary, but it allows zeep to parse imperfect XML
settings = Settings(strict=False, xml_huge_tree=True)

def get_model(ENUM):

    client = Client(AXL_WSDL_URL, settings=settings, transport=transport, plugins=[MyLoggingPlugin(),history])

    service = client.create_service("{http://www.cisco.com/AXLAPIService/}AXLAPIBinding", AXL_CUCM_URL)

    cmd = 'select name from typemodel where enum=' + str(ENUM)

    sql_cmd = {
        'sql' : cmd
    }

    try:
    	sql_resp = service.executeSQLQuery(**sql_cmd)
    except Fault as err:
    	print("Zeep error: {0}".format(err))
    else:
        Obj = sql_resp['return']['row'][0]
        modelObj = Obj[0]
        MODEL = modelObj.text
        return(MODEL)

    #ipps_file='CLASS01-MENU.xml'

class Dialog(QDialog):

    def __init__(self):
        super(Dialog,self).__init__()

        self.createHorizontalGroupBox()
        self.phoneList = {}

        self.bigEditor = QTextEdit()
        self.bigEditor.setPlainText("")

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.leftLayout)
        mainLayout.addWidget(self.bigEditor)
        self.setLayout(mainLayout)
        self.setGeometry(100,100,600,600)
        self.setWindowTitle('IPPS Tester')

        self.getPhones()
        self.opChange()
        self.populateIPPS()

    def createHorizontalGroupBox(self):

        self.leftLayout = QGroupBox()

        phoneLabel = QLabel("Select Phone:")
        modelLabel = QLabel("Select Model:")
        ipLabel = QLabel("IP Address:")
        enumLabel = QLabel("Model Enum:")
        self.ipAddress = QLabel(" ")
        self.Enum = QLabel(" ")
        opLabel = QLabel("Select IPPS Operation")
        self.phoneBox = QComboBox()
        self.phoneBox.currentIndexChanged.connect(self.phoneChange)
        self.modelBox = QComboBox()
        self.modelBox.setDuplicatesEnabled(True)
        self.modelBox.currentIndexChanged.connect(self.modelChange)
        self.opBox = QComboBox()
        self.opBox.currentIndexChanged.connect(self.opChange)
        self.goButton = QPushButton("Send To Phone")
        self.goButton.clicked.connect(self.sendIPPS)
        self.quitButton = QPushButton("Quit")
        self.quitButton.clicked.connect(self.quitApp)

        layout = QVBoxLayout()

        topLayout = QHBoxLayout()
        topLayout.addWidget(phoneLabel)
        topLayout.addWidget(self.phoneBox)

        midLayout = QHBoxLayout()
        midLayout.addWidget(modelLabel)
        midLayout.addWidget(self.modelBox)
        self.modelBox.setDuplicatesEnabled(False)

        ipLayout = QHBoxLayout()
        ipLayout.addWidget(ipLabel)
        ipLayout.addWidget(self.ipAddress)
        ipLayout.addWidget(enumLabel)
        ipLayout.addWidget(self.Enum)

        opLayout = QHBoxLayout()
        opLayout.addWidget(opLabel)
        opLayout.addWidget(self.opBox)

        botLayout = QHBoxLayout()
        botLayout.addWidget(self.goButton)
        botLayout.addWidget(self.quitButton)

        layout.addLayout(topLayout)
        layout.addLayout(midLayout)
        layout.addLayout(ipLayout)
        layout.addLayout(opLayout)
        layout.addLayout(botLayout)

        self.leftLayout.setLayout(layout)

    def phoneChange(self, i):
        self.modelBox.setCurrentIndex(i)
        name = self.phoneBox.currentText()
        self.ipAddress.setText(self.phoneList[name]['ip'])
        self.Enum.setText(str(self.phoneList[name]['enum']))
        self.populateIPPS()

    def modelChange(self, i):
        self.phoneBox.setCurrentIndex(i)
        name = self.phoneBox.currentText()
        self.ipAddress.setText(self.phoneList[name]['ip'])
        self.Enum.setText(str(self.phoneList[name]['enum']))
        self.populateIPPS()

    def opChange(self):
        index = self.phoneBox.currentIndex()
        self.modelBox.setCurrentIndex(index)
        op = self.opBox.currentText()
        if (len(op) > 0):
            name = self.phoneBox.currentText()
            model = self.phoneList[name]['model']
            with open("CLASSES.json") as json_file:
                data = json.load(json_file)
            pclass = data[model]
            ipps_file = pclass+'-'+op+'.xml'
            file = open(ipps_file,'r')
            thexml = file.read()
            self.bigEditor.setPlainText(thexml)

    def populateIPPS(self):
        index = self.phoneBox.currentIndex()
        self.modelBox.setCurrentIndex(index)
        name = self.phoneBox.currentText()
        model = self.phoneList[name]['model']
        with open("CLASSES.json") as json_file:
            data = json.load(json_file)
        pclass = data[model]
        pclass = "CLASS01"
        opsFile = pclass+'-OPS.list'
        with open(opsFile,'r') as filehandle:
            items = json.load(filehandle)
        self.opBox.clear()
        for item in items:
            self.opBox.addItem(item)

    def sendIPPS(self):
        name = self.phoneBox.currentText()
        ip = self.phoneList[name]['ip']
        doc = self.bigEditor.toPlainText()

        client = Client(WSDL_URL, settings=settings, transport=transport, plugins=[MyLoggingPlugin(),history])
        service = client.create_service("{http://schemas.cisco.com/ast/soap}RisBinding", CUCM_URL)

        up = PUSERNAME+':'+PPASSWD
        xml = "XML=" + doc
        headers = {"Content-Type": "application/xml"}
        r = requests.post('http://' + up + '@' + ip + '/CGI/Execute', data=xml, headers=headers)
        print("\nPhone response:\n")
        print(r, r.content)

    def quitApp(self):
        app.quit()

    def getPhones(self):

        client = Client(WSDL_URL, settings=settings, transport=transport, plugins=[MyLoggingPlugin(),history])
        service = client.create_service("{http://schemas.cisco.com/ast/soap}RisBinding", CUCM_URL)

        phone_data = {
            'StateInfo': '',
            'CmSelectionCriteria' : {
                'MaxReturnedDevices' : '1000',
                'DeviceClass' : 'Phone',
                'Model' : '255',
                'Status' : 'Registered',
                'NodeName' : '',
                'SelectBy' : 'Description',
                'SelectItems' : {
                    'item' : {
                        'Item' : '*'
                    }
                }
            }
        }

        try:
        	cm_resp = service.selectCmDevice(**phone_data)
        except Fault as err:
        	print("Zeep error: {0}".format(err))
        else:
            DevFound = cm_resp['SelectCmDeviceResult']['TotalDevicesFound']
            for x in range(DevFound):
                device = cm_resp['SelectCmDeviceResult']['CmNodes']['CmNode'][0]['CmDevices']['CmDevice'][x]
                newPhone = {}
                if device['Httpd'] == 'Yes':
                    name = device['Name']
                    ip = device['IpAddress']
                    ENUM = device['Model']
                    model = get_model(ENUM)
                    newPhone["ip"] = ip
                    newPhone["enum"] = ENUM
                    newPhone["model"] = model
                    self.phoneList[name] = newPhone

            for name in self.phoneList:
                self.phoneBox.addItem(name)
                self.modelBox.addItem(self.phoneList[name]['model'])
                self.ipAddress.setText(self.phoneList[name]['ip'])
                self.Enum.setText(str(self.phoneList[name]['enum']))
            self.phoneBox.setCurrentIndex(0)
            self.modelBox.setCurrentIndex(0)
            name = self.phoneBox.currentText()
            self.ipAddress.setText(self.phoneList[name]['ip'])
            self.Enum.setText(str(self.phoneList[name]['enum']))



if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    dialog=Dialog()
    sys.exit(dialog.exec_())
