# Import libraries
import sys
import logging
import getpass
import sleekxmpp
import time
import ssl

from optparse import OptionParser
from sleekxmpp.exceptions import IqError, IqTimeout
from menu import *


# Principal Class -> USER
class EchoBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, nick, room):

        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        # Nick and room
        self.room = room
        self.nick = nick

        # Event handlers
        self.add_event_handler("session_start", self.start, threaded=True)
        self.add_event_handler("message", self.message)
        self.add_event_handler("register", self.register, threaded=True)
        self.add_event_handler("groupchat_message", self.gp_msg, threaded=True)
        self.add_event_handler("muc::%s::got_online" % self.room, self.gp_chat, threaded=True)

    # Process event: session_start
    def start(self, event):
        print("\nSession start")
        print("°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°°")
        self.send_presence()
        self.get_roster()

    # Receive message
    def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            print("\n", msg['from'], "says: ")
            print("==> ", msg['body'], "\n")

    # Register
    def register(self, iq):
        resp = self.Iq()
        resp['type'] = 'set'
        resp['register']['username'] = self.boundjid.user
        resp['register']['password'] = self.password
        try:
            resp.send(now=True)
            logging.info("Succesfull register: %s!" % self.boundjid)
        except IqError as e:
            logging.error("Error: unable to register %s" %
                          e.iq['error']['text'])
            self.disconnect()
        except IqTimeout:
            logging.error("Error: no response from server")
            self.disconnect()

    # Get all users and print them
    def get_users(self):
        print(self.client_roster)

    # Delete user from server
    def delete_user(self):
        resp = self.Iq()
        resp['type'] = 'set'
        resp['from'] = self.boundjid.user
        resp['register'] = ' '
        resp['register']['remove'] = ' '
        try:
            resp.send(now=True)
            print("Account deleted for %s!" % self.boundjid)
        except IqError as e:
            logging.error("Could not delete account: %s" %
                          e.iq['error']['text'])
            self.disconnect()
        except IqTimeout:
            logging.error("No response from server.")
            self.disconnect()

    def gp_msg(self, msg):
        if msg['mucnick'] != self.nick and self.nick in msg['body']:
            print("%(body)s" % msg)

    def gp_chat(self, presence):
        if presence['muc']['nick'] != self.nick:
            self.send_message(mto=presence['from'].bare,
                              mbody="Hello, %s %s" % (presence['muc']['role'],
                                                      presence['muc']['nick']),
                              mtype='groupchat')

    # Send files to another user
    def send_files(self, receiver, filename):
        stream = self['xep_0047'].open_stream(receiver)
        with open(filename) as f:
            data = f.read()
            stream.sendall(data)


if __name__ == '__main__':
    optp = OptionParser()

    # Verbose
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # Information: jid, password, to, message
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-t", "--to", dest="to",
                    help="JID to send the message to")
    optp.add_option("-m", "--message", dest="message",
                    help="message to send")
    optp.add_option("-n", "--nick", dest="nick",
                    help="MUC nickname")
    optp.add_option("-r", "--room", dest="room",
                    help="MUC room to join")

    opts, args = optp.parse_args()

    # Login
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    # Call function menu()
    optmen = int(menu())

    # Add credentials
    username = input("Username: ")
    opts.jid = username + "@redes2020.xyz"
    opts.password = getpass.getpass("Password: ")
    opts.nick = input("Nickname: ")
    opts.room = "alumnos@conference.redes2020.xyz"

    xmpp = EchoBot(opts.jid, opts.password, opts.nick, opts.room)
    if (optmen == 2):
        xmpp.del_event_handler("register", xmpp.register)

    # Register plugins
    xmpp.register_plugin('xep_0004')  # Data forms
    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0045')  # Multichat
    xmpp.register_plugin('xep_0060')  # PubSub
    xmpp.register_plugin('xep_0066')  # Out-of-band Data
    xmpp.register_plugin('xep_0077')  # In-band Registration
    xmpp.register_plugin('xep_0199')  # Ping
    xmpp['xep_0077'].force_registration = True

    # authentication over an unencrypted connection
    xmpp['feature_mechanisms'].unencrypted_plain = True
    xmpp.ssl_version = ssl.PROTOCOL_TLS

    # Server connection
    # if xmpp.connect():
    if xmpp.connect(('@redes2020.xyz', True)):
        xmpp.process(block=False)  # True or false?
        # Principal menu
        while (1):
            choice = int(menu_in())
            # Show all users
            if (choice == 1):
                print("Contacts: \n")
                print(xmpp.client_roster)
                """
                i = 0 
                y = 0
                for i in range (len(xmpp.client_roster)):
                    print(xmpp.client_roster[i][y])
                    i = i + 1
                """
            # Add user
            elif (choice == 2):
                new_contact = input("username: \n")
                friend = new_contact + "@redes2020.xyz"
                xmpp.send_presence(pto=friend, ptype='subscribe')

            # Show details from an specific user
            elif (choice == 3):
                print("\n ", xmpp.client_roster, "\n")

                # Direct message
            elif (choice == 4):
                print("\nPRIVATE CHAT\n")
                username = input("\n To: ")
                user_to = username + "@redes2020.xyz"
                content = input("\n Content: ")
                xmpp.send_message(mto=user_to, mbody=content, mtype='chat')
                print("\n SENT \n")

            # Send presence message and change status
            elif (choice == 5):
                status = input("Status: ")
                flag = 0
                while (flag == 0):
                    sh = int(show_menu())
                    flag = 1
                    if (sh == 1):
                        show = "chat"
                    elif (sh == 2):
                        show = "away"
                    elif (sh == 3):
                        show = "xa"
                    elif (sh == 4):
                        show = "dnd"
                    else:
                        print("Please, try again")
                        flag = 0

                """
                self.send_presence(pstatus="i'm not around right now", pshow='xa')
                Where pstatus controls the type of icon your IM client will show, and you
                have the options of: chat, away, xa, and dnd. The value 'xa' means
                extended away and 'dnd' means do not disturb.
                """
                xmpp.makePresence(pfrom=xmpp.jid, pstatus=status, pshow=show)

            # Public chat
            elif (choice == 6):
                xmpp.plugin['xep_0045'].joinMUC(xmpp.room, xmpp.nick)
                print("\nPUBLIC CHAT\n")
                msg_all = input("Message: ")
                xmpp.send_message(mto='all', mbody=msg_all, mtype='groupchat')
                print("\n SENT \n")

            # Send file
            elif (choice == 7):
                username = input("\n To: ")
                send_to = username + "@redes2020.xyz"
                file = input("File: ")
                xmpp.send_files(send_to, file)

            # Exit
            elif (choice == 8):
                print("See you later")
                xmpp.disconnect()
                break

            # Delete account
            elif (choice == 9):
                xmpp.delete_user()
                xmpp.disconnect()
                break

            # If the option is not between (1-10)
            else:
                print("Invalid option")

    # Fail connection
    else:
        print("Unable to connect :(")