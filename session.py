# proyecto 2 de redes
# chat con XMPP
# Sergio Marchena
# 16387

from slixmpp import ClientXMPP
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.xmlstream.asyncio import asyncio
from threading import Thread
from menu import menu
import logging
import sys
import uuid
import blessed

# Start the blessed terminal used for UI
term = blessed.Terminal()

# Available statuses to change to
status = [
    'available',
    'unavailable'
]


class Session(ClientXMPP):

    def __init__(self, jid, password, nick):
        ClientXMPP.__init__(self, jid, password)
        """ Add all event handlers, nickname and
        start reciever in alumnchat """
        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("socks5_connected", self.stream_opened)
        self.add_event_handler("socks5_data", self.stream_data)
        self.add_event_handler("socks5_closed", self.stream_closed)
        self.room = 'alumnos'
        self.nick = nick
        self.current_reciever = 'alumchat.xyz'
        self.auto_subscribe = True
        # Functions sent as arguments to main menu
        functions = {
            'dc': self.dc_and_exit,
            'list': self.get_contacts,
            'add': self.add_contact,
            'peek': lambda args: print('looking....'),
            'jr': self.join_room,
            'lr': self.leave_room,
            'cpm': self.change_status,
            'sf': self.send_file,
            'rm': self.delete_account,
            'send_message': self.message_sender,
            'jc': self.join_conversation
        }
        self.menuInstance = Thread(target=menu, args=(functions,))
        # self.add_event_handler("register", self.register)

    def session_start(self, event):
        """ Handler for successful connection,
        start the menu thread """
        self.send_presence()
        self.get_roster()
        self.menuInstance.start()

    def dc_and_exit(self, args):
        """ Disconect from server and exit the
        program
        BUG: For some reason after using blessed's
        fullscreeen sys.exit() doesn't exit the program correctly """
        self.disconnect(wait=2.0)
        sys.exit()
        sys.exit()

    def message_error(self, msg):
        """ Error messages """
        print(term.bold_red('ha ocurrido un error'))
        print(msg)

    def message(self, msg):
        """ Handler for normal messages """
        if msg['type'] in ('chat', 'normal'):
            print(term.magenta(str(msg['from']) + ' > ') + term.color(55)(msg['body']))

    def muc_message(self, msg):
        """ Handler for group messages, displayed
        in a different color """
        print(term.cyan(str(msg['from']) + ' > ') + term.color(181)(msg['body']))
        print(msg['from'].bare)

    def muc_online(self, presence):
        """ This triggers when people enter the group chat
        we send a welcome to the new user
        TODO: handle presence['from'] to make
        sending messages to group easier """
        if presence['muc']['nick'] != self.nick:
            print(term.bold(presence['muc']['nick'] + ' se ha unido a la sala'))
            self.send_message(mto=presence['from'].bare,
                              mbody="Hello, %s %s" % (presence['muc']['role'], presence['muc']['nick']),
                              mtype='groupchat')

    """ The following 3 handlers are for opening, recieving
    and close the send file stream respectively 
    The recieved file is copied to a txt with a unique id
    given by uuid()
    NOTE: Untested """

    def stream_opened(self, sid):
        logging.info('Stream opened. %s', sid)
        self.file = open(str(uuid.uuid4()) + '.txt', 'wb')

    def stream_data(self, data):
        self.file.write(data)

    def stream_closed(self, exception):
        logging.info('Stream closed. %s', exception)
        self.file.close()

    def join_room(self, room):
        """ Join a room, this works! """
        self.add_event_handler("muc::%s::got_online" % room, self.muc_online)
        self.plugin['xep_0045'].join_muc(room, self.nick, wait=True)
        self.room = room
        print(term.bold_green('Conectado a room: ' + room))

    def leave_room(self, msg=''):
        """ Leave a room, this works too! """
        try:
            self.plugin['xep_0045'].leave_muc(self.jid, self.nick, msg)
            print(term.bold_red('Desconectado de room: ' + self.room))
            self.room = ''
        except KeyError:
            print(term.bold_red(
                "muc.leave_groupchat: could not leave the room %s",
                self.jid))

    def add_contact(self, contact):
        """ Add contact to contact list
        TODO: Currently no handling of error when adding user """
        self.send_presence_subscription(pto=contact)
        print(term.bold_green(contact + ' es ahora tu contacto'))

    def get_contacts(self, args):
        """ Print all contacts on contact list """
        print(term.magenta('Users in your contact list: '))
        for jid in self.roster[self.jid]:
            print(term.cyan(jid))

    def change_status(self, args):
        """ Change status given it is in the valid list """
        if args in status:
            self.make_presence(pshow=args)
            print(term.bold_green('Estatus cambiado'))
        else:
            print(term.bold_red('Estado no valido'))

    def join_conversation(self, args):
        """ Method used to change the guy we are currently speaking to
        returns an error in case that user is not in our contacts list """
        if args in self.roster[self.jid]:
            self.current_reciever = args
        else:
            print(term.bold_red('ERROR: Usuario no en la lista de contactos'))

    def message_sender(self, args):
        """ Send normal message
        TODO: Make it alternate between muc and normal given the conversation context """
        self.send_message(mto=self.current_reciever, mbody=args, msubject='normal message', mfrom=self.boundjid)

    def file_sender(self, args):
        """ Helper function to run file send """
        asyncio.run(self.send_file(args))

    async def send_file(self, args):
        params = args.strip().split()
        try:
            file = open(params[0], 'rb')
            # Open the S5B stream in which to write to.
            proxy = await self['xep_0065'].handshake(params[1])
            # Send the entire file.
            while True:
                data = file.read(1048576)
                if not data:
                    break
                await proxy.write(data)
                proxy.transport.write_eof()
        except (IqError, IqTimeout):
            print('File transfer errored')
        else:
            print('File transfer finished')
        finally:
            file.close()

    def delete_account(self, args):
        """ Helper function to delete account """
        asyncio.run(self.delete_account_send())

    async def delete_account_send(self):
        # Manual build of delete account iq
        resp = self.Iq()
        resp['type'] = 'set'
        resp['from'] = self.boundjid.jid
        resp['register'] = ' '
        resp['register']['remove'] = ' '
        try:
            await resp.send()
            print('')
        except IqError:
            print(term.bold_red('Error al eliminar cuenta'))
        except IqTimeout:
            print(term.bold_red('timeout'))
            self.disconnect()

    async def register(self, iq):
        """ Register function, calls itself every time.
        If your accont already exists it does nothing, if
        it is new, it registers you
        TODO: Find way to skip this function if your account
        already exists """
        resp = self.Iq()
        resp['type'] = 'set'
        resp['register']['username'] = self.boundjid.user
        resp['register']['password'] = self.password
        try:
            await resp.send()
            logging.info("Account created for %s!" % self.boundjid)
        except IqError as e:
            logging.error("Could not register account: %s" % e.iq['error']['text'])
        except IqTimeout:
            logging.error("No response from server.")
            self.disconnect()
