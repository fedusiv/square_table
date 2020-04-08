import sys
import socket
import time
import threading
import json
import queue
import communication_protocol as CP
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QLineEdit, QMessageBox,
                                QHBoxLayout, QVBoxLayout)
from PyQt5.QtCore import QObject, pyqtSignal

#
# Clinet Class - Communication with Server
#
class Client(QObject):
    port = 12345
    _sock_run = False   # if True runs client socket connection
    player_name = None  
    thread_lock = None  # thread lock, for safe thread 
    message_queue = None
    # signals field
    signal_clientconnected = pyqtSignal()   # when client connected to server emit signal
    signal_keepalive = pyqtSignal('PyQt_PyObject')  # when received keepalive message

    def __init__(self):
        super().__init__()
        self.message_queue = queue.Queue()  # init infinite queue. hope it will not occur any problems

    def connect_to_server(self, server, name):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((server, self.port))
        self.player_name = name
        if self.greeting_server() is False:
            sys.exit(1)
        self.signal_clientconnected.emit()
        self._sock_run = True
        self.thread_lock = threading.Lock()
        self.client_thread = threading.Thread(name="client", target=self.threaded)
        self.client_thread.start()

    def close_connection(self):
        # send bye bye message to server
        self.sock.send(bytes(json.dumps({"type": CP.EXIT_TYPE, "player_name": self.player_name}), 'UTF-8'))
        # exit frim communication thread
        self.thread_safe_change_single_var( self._sock_run, False)
        if self.sock is not None:
            self.sock.close()
    
    def threaded(self):
        data = threading.local() # variables local for thread
        data.server_keepalive_count = 20
        data.server_keepalive_counter = 0
        # set timeout to one second. 
        self.sock.settimeout(1)
        while self._sock_run:
            # delivery is message for send
            delivery = self.get_message_from_queue_for_send()
            if delivery is not None:
                self.sock.send(bytes(delivery)) # send message to server

            try:
                received = json.loads(self.sock.recv(1024).decode('UTF-8'))
                # message received keep alive to 0
                data.server_keepalive_counter = 0
                # received keepalive
                if received["type"] == CP.KEEPALIVE_TYPE:
                    if received["player_name"] == self.player_name:
                        self.sock.send(bytes(json.dumps({"type": CP.KEEPALIVE_TYPE, "status": CP.STATUS_OK}),'UTF-8'))
                        self.signal_keepalive.emit(received)
            
            except socket.timeout:
                data.server_keepalive_counter+=1
                if data.server_keepalive_counter > data.server_keepalive_count :
                    print("No connection with server")
                    break
        # close the connection
        self.sock.close()
    
    #Say Hello to server
    def greeting_server(self):
        message = {"type":CP.GREETING_TYPE, "player_name": self.player_name}
        while True:
            self.sock.send(bytes(json.dumps(message), 'UTF-8'))
            answer = json.loads(self.sock.recv(1024).decode('UTF-8'))
            if answer["type"] == CP.GREETING_TYPE:
                if answer["status"] == CP.STATUS_OK:
                    if answer["player_name"] == self.player_name:
                        return True
                else:
                    return False
            #just wait for another try
            time.sleep(1)

    # Player chose role to play
    def send_choosen_role(self,role):
        message = json.dumps( {"type": CP.CHOOSE_ROLE,"player_name" : self.player_name, "role": role})
        self.put_message_to_queue_for_send(message)

    # put message to queue for send to server
    def put_message_to_queue_for_send(self, message):
        self.thread_lock.acquire()
        self.message_queue.put(message)
        self.thread_lock.release()

    # thread safe take first message for send to server
    def get_message_from_queue_for_send(self):
        var = None
        self.thread_lock.acquire()
        if not self.message_queue.empty() :
            var = self.message_queue.get()
        self.thread_lock.release()
        return var

    # method change variable in thread safe way
    def thread_safe_change_single_var(self,var,value):
        self.thread_lock.acquire()
        var = value
        self.thread_lock.release()
#
# Gui - Main Thread
#
class Gui(QWidget):
    def __init__(self):
        super().__init__()
        self.client = Client()
        self.signals_init()
        self.initUI()

    # All signals should be initilized here
    def signals_init(self):
        self.client.signal_clientconnected.connect(self.on_client_connected_to_server)
        self.client.signal_keepalive.connect(self.on_client_keepalive)

    def initUI(self):
        self.setFixedSize(150,200)
        self.setWindowTitle('Square Table')
        self.show()

        self.connectWindow()

    def connectWindow(self):
        self.qlabel_connect_address = QLabel(parent=self)
        self.qlabel_connect_address.move(10, 10)
        self.qlabel_connect_address.setText("Enter server address")
        self.qlabel_connect_address.show()

        self.qlineedit_server_address = QLineEdit(self)
        self.qlineedit_server_address.move(10, 30)
        self.qlineedit_server_address.show()

        self.qlabel_connect_nickname = QLabel(parent=self)
        self.qlabel_connect_nickname.move(10, 70)
        self.qlabel_connect_nickname.setText("Enter your name")
        self.qlabel_connect_nickname.show()

        self.qlineedit_connect_nickname = QLineEdit(self)
        self.qlineedit_connect_nickname.move(10, 90)
        self.qlineedit_connect_nickname.show()

        self.qbutton_connect = QPushButton(parent=self,text="Connect")
        self.qbutton_connect.resize(self.qbutton_connect.sizeHint())
        self.qbutton_connect.move(30,130)
        self.qbutton_connect.show()
        self.qbutton_connect.clicked.connect(self.on_connect_to_server_clicked)

    # hide start-connect window
    def connectWindowClose(self):
        self.qlabel_connect_address.hide()
        self.qlabel_connect_nickname.hide()
        self.qlineedit_connect_nickname.hide()
        self.qlineedit_server_address.hide()
        self.qbutton_connect.hide()

    # Status bar, which dosplays server connection status
    def connectionStatusBarInit(self):
        self.qlabel_connectionStatus = QLabel()
        self.qlabel_connectionNickName = QLabel()
        self.qlabel_connectionServerTime = QLabel()
        self.layoutStatusBar = QHBoxLayout()
        self.layoutStatusBar.addWidget(self.qlabel_connectionStatus)
        self.layoutStatusBar.addWidget(self.qlabel_connectionNickName)
        self.layoutStatusBar.addWidget(self.qlabel_connectionServerTime)

    def chooseRoleWindow(self):
        self.connectWindowClose()
        self.setFixedSize(700,350)

        # Description layout
        label_generalDesc = QLabel(self)
        label_generalDesc.setText("General\nDescription")
        label_diplomatDesc = QLabel(self)
        label_diplomatDesc.setText("Diplomat\nDescription")
        label_bishopDesc = QLabel(self)
        label_bishopDesc.setText("Bishop\nDescription")
        label_treasurerDesc = QLabel(self)
        label_treasurerDesc.setText("Treasurer\nDescription")
        label_manufacturerDesc = QLabel(self)
        label_manufacturerDesc.setText("Manufacturer\nDescription")
        
        layoutDesc = QHBoxLayout()
        layoutDesc.addWidget(label_generalDesc)
        layoutDesc.addWidget(label_diplomatDesc)
        layoutDesc.addWidget(label_bishopDesc)
        layoutDesc.addWidget(label_manufacturerDesc)
        layoutDesc.addWidget(label_treasurerDesc)

        #Chose Role Buttons layout
        self.qbutton_chooseGeneral      = QPushButton(text="General")
        self.qbutton_chooseGeneral.clicked.connect(self.on_clicked_choose_role)
        self.qbutton_chooseDiplomat     = QPushButton(text="Diplomat")
        self.qbutton_chooseDiplomat.clicked.connect(self.on_clicked_choose_role)
        self.qbutton_chooseBishop       = QPushButton(text="Bishop")
        self.qbutton_chooseTreasurer    = QPushButton(text="Treasure")
        self.qbutton_chooseManufacturer = QPushButton(text="Manufacturer")
        

        layoutButtons = QHBoxLayout()
        layoutButtons.addWidget(self.qbutton_chooseGeneral     )
        layoutButtons.addWidget(self.qbutton_chooseDiplomat    )
        layoutButtons.addWidget(self.qbutton_chooseBishop      )
        layoutButtons.addWidget(self.qbutton_chooseManufacturer)
        layoutButtons.addWidget(self.qbutton_chooseTreasurer   )

        #Additional Buttons Layout
        self.qbutton_chooseRandomRole = QPushButton(text="Choose Random Role")
        layoutAdButtons = QHBoxLayout()
        layoutAdButtons.addWidget(self.qbutton_chooseRandomRole)

        self.layoutChooseRole = QVBoxLayout(self)
        self.layoutChooseRole.addLayout(self.layoutStatusBar)
        self.layoutChooseRole.addLayout(layoutDesc)
        self.layoutChooseRole.addLayout(layoutButtons)
        self.layoutChooseRole.addLayout(layoutAdButtons)
        
        self.setLayout(self.layoutChooseRole)

    #Handler Signal from Button to connect to server
    def on_connect_to_server_clicked(self):
        if self.qlineedit_connect_nickname.text() == "":
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setText("No name specified")
            msg.show()
            return
        if self.qlineedit_server_address.text() == "":
            self.qlineedit_server_address.setText("127.0.0.1")
        
        self.client.connect_to_server(self.qlineedit_server_address.text(), self.qlineedit_connect_nickname.text())

    def closeEvent(self, event):
        #close client connection
        self.client.close_connection()

    #when client connected to server
    def on_client_connected_to_server(self):
        self.connectWindowClose()   #close previous window
        self.connectionStatusBarInit()  #init layout for connection status bar. 
        self.chooseRoleWindow()         # init next window 

    # Handler received keepalive, fill status bar
    def on_client_keepalive(self, message):
        self.qlabel_connectionStatus.setText("Connected")
        self.qlabel_connectionNickName.setText("Name : " + message["player_name"])
        self.qlabel_connectionServerTime.setText(message["server_time"])

    # Handler choosing role buttons. And jsut send information to server.
    def on_clicked_choose_role(self, role):
        button = self.sender()
        role = None
        if button == self.qbutton_chooseGeneral :
            role = CP.GENERAL
        elif button == self.qbutton_chooseDiplomat :
            role = CP.DIPLOMAT
        elif button == self.qbutton_chooseManufacturer:
            role = CP.MANUFACTURER
        elif button == self.qbutton_chooseBishop:
            role = CP.BISHOP
        elif button == self.qbutton_chooseTreasurer:
            role = CP.TREASURER
        elif button == self.qbutton_chooseRandomRole:
            role = CP.ROLE_RANDOM
        # say client to send player decision
        self.client.send_choosen_role(role)
        
def main():
    app = QApplication(sys.argv)
    gui = Gui()
    sys.exit(app.exec_())


main()