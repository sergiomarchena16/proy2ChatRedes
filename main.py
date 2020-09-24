# PROYECTO 2 CHAT DE XMPP
# SERGIO MARCHENA
# 16387

# LIBRARIES
from sleekxmpp import ClientXMPP
from sleekxmpp.xmlstream.stanzabase import ET
from sleekxmpp.exceptions import IqError, IqTimeout
import sleekxmpp
from prettytable import PrettyTable
from tkinter import filedialog
import base64
import time

# Get file's path
def my_file():
    image_formats = [("JPEG", "*.jpg"), ("JPG", "*.jpeg"), ("PNG", "*.png")]
    filename = filedialog.askopenfilename(initialdir="C:/", title="select file", filetypes=image_formats)

    return filename

class User():
    # Initialize User variables
    def __init__(self, user, status, show, subscription, online):
        self.user = user
        self.show = show
        self.status = status
        self.subscription = subscription
        self.online = online

    # Set state of User
    def set_states(self, status, show):
        self.status = status
        self.show = show

    # Change online in on/off
    def set_online(self, online):
        self.online = online

    # Get User username
    def get_username(self):
        return self.user

    # Get all info of User
    def get_usuario(self):
        return [self.user, self.status, self.show, self.online, self.subscription]


class Client(ClientXMPP):

    # Initialize Client variables
    def __init__(self, jid, password):
        ClientXMPP.__init__(self, jid, password)
        self.timeout = 45
        self.my_jid = jid.lower()
        self.usuarios = []
        self.rooms = {}
        self.contador_rooms = 1

        # Manage all events
        self.add_event_handler('session_start', self.session_start)
        self.add_event_handler('message', self.message)
        self.add_event_handler('changed_status', self.on_presence)
        self.add_event_handler("presence_unsubscribe", self.presence_unsubscribe)
        self.add_event_handler("presence_subscribe", self.presence_subscribe)
        self.add_event_handler("got_offline", self.got_offline)
        self.add_event_handler("got_online", self.got_online)

        # Register all plug-ins
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0199')  # XMPP Ping
        self.register_plugin('xep_0004')  # Data forms
        self.register_plugin('xep_0077')  # In-band Registration
        self.register_plugin('xep_0045')  # Mulit-User Chat (MUC)
        self.register_plugin('xep_0096')  # File transfer

        import ssl
        self.ssl_version = ssl.PROTOCOL_TLS

    # Trigger when someone unsubscribe
    def presence_unsubscribe(self, presence):
        person = self.jid_to_user(presence['from'])
        print(person + 'te elimno' )
        for i in range(len(self.usuarios)):
            if self.usuarios[i].get_username() == person:
                self.usuarios.pop(i)
                break

    # Trigger when someone subscribe
    def presence_subscribe(self, presence):
        person = self.jid_to_user(presence['from'])
        print(person + ' te agrego como amigo')
        self.SendMessageTo(presence['from'], 'agregado')
        usr = User(person, '---', '---', 'both', 'No')
        self.usuarios.append(usr)

    # Trigger when someone got offline
    def got_offline(self, presence):
        if self.boundjid.bare not in str(presence['from']):
            usr = self.jid_to_user(str(presence['from']))
            print(usr + ' esta online' )
            for i in self.usuarios:
                if i.get_username() == usr:
                    i.set_online('No')
                    break

    # Trigger when someone got online
    def got_online(self, presence):
        isGroup = self.IsGroup(str(presence['from']))
        if isGroup:
            nickname = str(presence['from']).split('@')[1].split('/')[1]
            groupname = str(presence['from']).split('@')[0]
            print(nickname + ' está en ' + groupname)
        else:
            if self.boundjid.bare not in str(presence['from']):
                usr = self.jid_to_user(str(presence['from']))
                print(usr + ' online')

                for i in self.usuarios:
                    if i.get_username() == usr:
                        i.set_online('Sí')
                        break

    # Trigger when User wants to connect to server
    def session_start(self, event):
        self.send_presence(pshow='chat', pstatus='este es mi status')
        roster = self.get_roster()
        for r in roster['roster']['items'].keys():
            subs = str(roster['roster']['items'][r]['subscription'])
            user = self.jid_to_user(str(r))
            if user != self.jid_to_user(self.my_jid):
                show = 'NaN'
                status = 'NaN'
                usr = User(user, status, show, subs, 'No')
                self.usuarios.append(usr)

    # Trigger when someone sends a private chat and groupchat
    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            if msg['subject'] == 'send_file' or len(msg['body']) > 500:
                img_body = msg['body']
                file_ = img_body.encode('utf-8')
                file_ = base64.decodebytes(file_)
                with open("redes_" + str(int(time.time())) + ".png", "wb") as f:
                    f.write(file_)
                print('\t==> %(from)s te envió un archivo...' % (msg) )
            else:
                print('\t==> [PRIVATELY: %(from)s] %(body)s' % (msg))
        if str(msg['type']) == 'groupchat':
            print('\t--> (%(from)s): %(body)s' % (msg) )

    # Trigger when someone changed status
    def on_presence(self, presence):
        user = str(presence['from'])
        user = self.jid_to_user(user)
        if user != self.jid_to_user(self.my_jid):
            if str(presence['type']) == 'unavailable':
                status = str(presence['type'])
                show = '-'
            else:
                if str(presence['status']):
                    status = str(presence['status'])
                else:
                    status = '-'
                if str(presence['show']):
                    show = str(presence['show'])
                else:
                    show = '-'
            encontrado = False
            index = 0
            for i in self.usuarios:
                if user in i.get_usuario():
                    encontrado = True
                    break
                index += 1
            if encontrado:
                self.usuarios[index].set_states(status, show)
            else:
                usr = User(user, status, show)
                self.usuarios.append(usr)

    # Check if jid has 'conference'
    def IsGroup(self, from_jid):
        if 'conference' in from_jid.split('@')[1]:
            return True
        else:
            return False

    # Send message to jid
    def SendMessageTo(self, jid, message):
        self.send_message(mto=jid, mbody=message, mtype='chat')

    # Send message to room
    def SendMessageRoom(self, room, message):
        self.send_message(mto=room, mbody=message, mtype='groupchat')

    # Let user to login
    def Login(self):
        success = False
        if self.connect():
            self.process()
            success = True
            print('Ingresado' )
        else:
            print('Algo paso' )
        return success

    # Send subscription presence to jid
    def AddUser(self, jid):
        self.send_presence_subscription(pto=jid)

    # Send file to jid
    def SendFile(self, path, to):
        with open(path, 'rb') as img:
            file_ = base64.b64encode(img.read()).decode('utf-8')
        self.send_message(mto=to, mbody=file_, msubject='send_file', mtype='chat')

    # Get a user info
    def GetUser(self, username):
        iq = self.Iq()
        iq['type'] = 'set'
        iq['id'] = 'search_result'
        iq['to'] = 'search.redes2020.xyz'

        item = ET.fromstring("<query xmlns='jabber:iq:search'> \
                                <x xmlns='jabber:x:data' type='submit'> \
                                    <field type='hidden' var='FORM_TYPE'> \
                                        <value>jabber:iq:search</value> \
                                    </field> \
                                    <field var='Username'> \
                                        <value>1</value> \
                                    </field> \
                                    <field var='search'> \
                                        <value>" + username + "</value> \
                                    </field> \
                                </x> \
                              </query>")
        iq.append(item)
        res = iq.send()

        data = []
        temp = []
        cont = 0
        for i in res.findall('.//{jabber:x:data}value'):
            cont += 1
            txt = ''
            if i.text == None:
                txt = '--'
            else:
                txt = i.text

            temp.append(txt)
            if cont == 4:
                cont = 0
                data.append(temp)
                temp = []

        us = []
        for i in self.usuarios:
            if username.lower() == i.get_username():
                us.append(i.get_usuario())
        return us, data

    # Get all users info
    def GetUsers(self):

        iq = self.Iq()
        iq['type'] = 'set'
        iq['id'] = 'search_result'
        iq['to'] = 'search.redes2020.xyz'

        item = ET.fromstring("<query xmlns='jabber:iq:search'> \
                                <x xmlns='jabber:x:data' type='submit'> \
                                    <field type='hidden' var='FORM_TYPE'> \
                                        <value>jabber:iq:search</value> \
                                    </field> \
                                    <field var='Username'> \
                                        <value>1</value> \
                                    </field> \
                                    <field var='search'> \
                                        <value>*</value> \
                                    </field> \
                                </x> \
                              </query>")
        iq.append(item)
        try:
            res = iq.send()
            data = []
            temp = []
            cont = 0
            for i in res.findall('.//{jabber:x:data}value'):
                cont += 1
                txt = ''
                if i.text == None:
                    txt = '--'
                else:
                    txt = i.text
                temp.append(txt)
                if cont == 4:
                    cont = 0
                    data.append(temp)
                    temp = []
            us = []
            for i in self.usuarios:
                us.append(i.get_usuario())
            return us, data
        except IqTimeout:
            print('TIME OUT')
            return [], []

    # Transform jid to only username
    def jid_to_user(self, jid):
        jid = str(jid)
        return jid.split('@')[0]

    # Remove a user from contact list
    def RemoveUser(self, jid):
        self.del_roster_item(jid)

        person = self.jid_to_user(jid)
        for i in range(len(self.usuarios)):
            if self.usuarios[i].get_username() == person:
                self.usuarios.pop(i)
                break

    # Change status of user
    def ChangeStatus(self, show, status):
        self.send_presence(pshow=show, pstatus=status)

    # Let user to join or create a room
    def JoinOrCreateRoom(self, room, nickname, creating):
        self.plugin['xep_0045'].joinMUC(room, nickname, wait=True)

        if creating:
            self.plugin['xep_0045'].setAffiliation(room, self.boundjid.full, affiliation='owner')
            self.plugin['xep_0045'].configureRoom(room, ifrom=self.boundjid.full)

        self.rooms[str(self.contador_rooms)] = room
        self.contador_rooms += 1

    # Remove user from server
    def Unregister(self):
        iq = self.make_iq_set(ito='redes2020.xyz', ifrom=self.boundjid.user)
        item = ET.fromstring("<query xmlns='jabber:iq:register'> \
                                <remove/> \
                              </query>")
        iq.append(item)
        try:
            res = iq.send()
            if res['type'] == 'result':
                print('ACC DELETED')
        except IqTimeout:
            print('TIMEOUT')

class RegisterNewUser(sleekxmpp.ClientXMPP):
    # Initialize variables
    def __init__(self, jid, password, name, email):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.name = name
        self.email = email

        self.add_event_handler('session_start', self.start)
        self.add_event_handler('register', self.register)

        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0004')  # Data forms
        self.register_plugin('xep_0066')  # Out-of-band Data
        self.register_plugin('xep_0077')  # In-band Registration

    # Trigger when user wants to connect
    def start(self, event):
        self.send_presence()
        self.get_roster()
        self.disconnect()

    # Used to register a new user in server
    def register(self, iq):
        resp = self.Iq()
        resp['type'] = 'set'
        resp['register']['username'] = self.boundjid.user
        resp['register']['password'] = self.password
        resp['register']['name'] = self.name
        resp['register']['email'] = self.email

        try:
            resp.send(now=True)
            print('Cuenta creada para ' + self.boundjid + '!')
        except IqError as e:
            print('NERROR')
            self.disconnect()
        except IqTimeout:
            print('TIME OUT')
            self.disconnect()


if __name__ == '__main__':
    domain = '@redes2020.xyz'
    show_state = {
        '1': 'sta1',
        '2': 'sta3',
        '3': 'sta2',
        '4': 'sta4'
    }

    FirstMenu = '''
.....................................................................................................................

1. Sign in 
2. Login

0. Exit
.....................................................................................................................
'''

    LoggedInMenu = '''
.....................................................................................................................

1. Show all users
2. Add a contact
3. Show details of a contact
4. Send private message
5. Rooms
6. Change status
7. Delete user
8. Send file
9. Delete account

0. Logout
.....................................................................................................................
'''
#######################################################
    # MENU
#######################################################
    o = ''
    hasLogin = False
    while o != '0':
        if not hasLogin:
            o = input(FirstMenu)

            if o == '1':
                username = input('username: ')
                password = input('password: ')
                name = input('full name: ')
                email = input('email: ')
                nuevoUsuario = RegisterNewUser(username + domain, password, name, email)
                if nuevoUsuario.connect():
                    nuevoUsuario.process(block=True)
                else:
                    print('FAIL')
            elif o == '2':
                username = input('username: ')
                password = input('password: ')
                xmpp = Client(username + domain, password)
                if xmpp.Login():
                    hasLogin = True
            elif o == '0':
                print('exited')
            else:
                print('??????')
        else:
            o = input(LoggedInMenu)
            if o == '1':
                users, server_users = xmpp.GetUsers()
                t2 = PrettyTable(['email', 'JID', 'username', 'name'])
                for i in server_users:
                    t2.add_row(i)
                print(t2)

            elif o == '2':
                user = input('JID: ')
                xmpp.AddUser(user)

            elif o == '3':
                contact = input('username: ')
                users, server_user = xmpp.GetUser(contact)
                t2 = PrettyTable(['Email', 'JID', 'Username', 'Name'])
                for i in server_user:
                    t2.add_row(i)
                print(t2)

            elif o == '4':
                to = input('JID: ')
                msg = input('message: ')
                xmpp.SendMessageTo(to, msg)
                print("sent")

            elif o == '5':
                o2 = input('1. Create room\n2. Join room\n3. Message room\n')
                if o2 == '1':
                    room = input('room name: ')
                    nickname = input('nickname: ')
                    xmpp.JoinOrCreateRoom(room, nickname, True)
                elif o2 == '2':
                    room = input('room: ')
                    nickname = input('nickname: ')
                    xmpp.JoinOrCreateRoom(room, nickname, False)
                elif o2 == '3':
                    for index, r in xmpp.rooms.items():
                        print(str(index) + '. ' + r)
                    room = input('room: ')
                    if room in xmpp.rooms.keys():
                        msg = input('message: ')
                        xmpp.SendMessageRoom(xmpp.rooms[room], msg)
                    else:
                        print('???')
                else:
                    print('???')

            elif o == '6':
                show_error = True
                while show_error:
                    show = input('status:\n 1. sta1\n 2. sta2\n 3. sta3\n 4. sta4\n')
                    if show in show_state.keys():
                        show_error = False
                status = input('new status: ')
                xmpp.ChangeStatus(show_state[show], status)

            elif o == '7':
                remove_to = input('username: ')
                xmpp.RemoveUser(remove_to)

            elif o == '8':
                path = my_file()
                if path:
                    to_person = input('jid: ')
                    xmpp.SendFile(path, to_person)

            elif o == '9':
                xmpp.Unregister()
                o = '0'

            if o == '0':
                xmpp.disconnect()
                o = ''
                hasLogin = False