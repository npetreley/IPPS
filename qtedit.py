import requests
import json
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
        self.setWindowTitle('IPPS Editor')

        self.getPhones()
        self.opChange()
        self.populateIPPS()

    def createHorizontalGroupBox(self):

        self.leftLayout = QGroupBox()

        modelLabel = QLabel("Select Model:")
        opLabel = QLabel("Select IPPS Operation")
        stLabel = QLabel("Status:")
        self.writestatus = QLabel(" ")
        self.modelBox = QComboBox()
        self.modelBox.setDuplicatesEnabled(True)
        self.modelBox.currentIndexChanged.connect(self.modelChange)
        self.opBox = QComboBox()
        self.opBox.currentIndexChanged.connect(self.opChange)
        self.saveButton = QPushButton("Save IPPS XML File")
        self.saveButton.clicked.connect(self.saveIPPS)
        self.loadButton = QPushButton("Load Default Template")
        self.loadButton.clicked.connect(self.loadIPPS)
        self.quitButton = QPushButton("Quit")
        self.quitButton.clicked.connect(self.quitApp)

        layout = QVBoxLayout()

        topLayout = QHBoxLayout()
        topLayout.addWidget(modelLabel)
        topLayout.addWidget(self.modelBox)
        self.modelBox.setDuplicatesEnabled(False)

        statLayout = QHBoxLayout()
        statLayout.addWidget(stLabel)
        statLayout.addWidget(self.writestatus)

        midLayout = QHBoxLayout()
        midLayout.addWidget(opLabel)
        midLayout.addWidget(self.opBox)

        botLayout = QHBoxLayout()
        botLayout.addWidget(self.saveButton)
        botLayout.addWidget(self.loadButton)
        botLayout.addWidget(self.quitButton)

        layout.addLayout(topLayout)
        layout.addLayout(midLayout)
        layout.addLayout(botLayout)
        layout.addLayout(statLayout)

        self.leftLayout.setLayout(layout)

    def quitApp(self):
        app.quit()

    def opChange(self):
        model = self.modelBox.currentText()
        op = self.opBox.currentText()
        if (len(op) > 0):
            pclass = self.phoneList[model]
            ipps_file = './'+pclass+'/'+op+'.xml'
            file = open(ipps_file,'r')
            thexml = file.read()
            self.bigEditor.setPlainText(thexml)

    def getPhones(self):
        with open('CLASSES.json') as json_file:
            self.phoneList = json.load(json_file)
        for x in self.phoneList.keys():
            self.modelBox.addItem(x)
        self.populateIPPS()

    def modelChange(self, i):
        self.modelBox.setCurrentIndex(i)
        model = self.modelBox.currentText()
        pclass = self.phoneList[model]
        opsFile = './'+pclass+'/OPS.list'
        with open(opsFile,'r') as filehandle:
            items = json.load(filehandle)
        self.opBox.clear()
        for item in items:
            self.opBox.addItem(item)
        self.populateIPPS()

    def populateIPPS(self):
        op = self.opBox.currentText()
        if (len(op) > 0):
            model = self.modelBox.currentText()
            pclass = self.phoneList[model]
            ipps_file = './'+pclass+'/'+op+'.xml'
            file = open(ipps_file,'r')
            thexml = file.read()
            self.bigEditor.setPlainText(thexml)

    def saveIPPS(self):
        self.writestatus.setText("Saving...")
        op = self.opBox.currentText()
        if (len(op) > 0):
            model = self.modelBox.currentText()
            pclass = self.phoneList[model]
            ipps_file = './'+pclass+'/'+op+'.xml'
            file = open(ipps_file,'w')
            doc = self.bigEditor.toPlainText()
            file.write(doc)
        loop = QEventLoop()
        QTimer.singleShot(2000, loop.quit)
        loop.exec_()
        self.writestatus.setText(" ")

    def loadIPPS(self):
        self.writestatus.setText("Loading...")
        op = self.opBox.currentText()
        if (len(op) > 0):
            ipps_file = './TEMPLATE/'+op+'.xml'
            file = open(ipps_file,'r')
            thexml = file.read()
            self.bigEditor.setPlainText(thexml)
        loop = QEventLoop()
        QTimer.singleShot(500, loop.quit)
        loop.exec_()
        self.writestatus.setText(" ")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    dialog=Dialog()
    sys.exit(dialog.exec_())
