import sys
import logging
import getpass
import sleekxmpp
from optparse import OptionParser
from sleekxmpp.exceptions import IqError, IqTimeout
from opciones import *
from sleekxmpp.stanza import Message, Presence, Iq, StreamError


class EchoBot(sleekxmpp.ClientXMPP):

    def __init__(self, jid, password, opcion):

        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        # Evento de login y registro
        if (opcion == '1'):
            self.add_event_handler("session_start", self.start)
        elif (opcion == '2'):
            self.add_event_handler("register", self.register)
            self.add_event_handler("session_start", self.start)

        self.add_event_handler("message", self.message)

        self.register_plugin('xep_0047', {
            'auto_accept': True
        })

        self.add_event_handler("ibb_stream_start", self.stream_opened, threaded=True)
        self.add_event_handler("ibb_stream_data", self.stream_data)

    # Procesa el evento session_start
    def start(self, event):
        print('Conectado')
        self.send_presence()
        self.get_roster()

    def accept_stream(self, iq):
        return True

    def stream_opened(self, stream):
        print('Stream opened: %s from %s' % (stream.sid, stream.peer_jid))

    def stream_data(self, event):
        print(event['data'])

    # Procesa los mensajes entrantes
    def message(self, msg):
        if msg['type'] in ('chat', 'normal'):
            print('------------------------------------------------------------------------------------------')
            print('From:')
            print(msg['from'])
            print('------------------------------------------------------------------------------------------')
            print(msg['subject'])
            print(msg['body'])
            print('------------------------------------------------------------------------------------------')

    def delete(self):
        resp = self.Iq()
        resp['type'] = 'set'
        resp['from'] = self.boundjid.user
        resp['register'] = ' '
        resp['register']['remove'] = ' '
        print(resp)
        try:
            resp.send(now=True)
            logging.info("Account deleted for %s!" % self.boundjid)
        except IqError as e:
            logging.error("Could not register account: %s" %
                          e.iq['error']['text'])
            self.disconnect()
        except IqTimeout:
            logging.error("No response from server.")
            self.disconnect()

    def send_file(self, filename, receiver):
        stream = self['xep_0047'].open_stream(receiver)

        with open(filename) as f:
            data = f.read()
            stream.sendall(data)

    def register(self, iq):
        resp = self.Iq()
        resp['type'] = 'set'
        resp['register']['username'] = self.boundjid.user
        resp['register']['password'] = self.password

        try:
            resp.send(now=True)
            logging.info("Se creo la cuenta: %s!" % self.boundjid)
        except IqError as e:
            logging.error("No se pudo registrar la cuenta %s" %
                          e.iq['error']['text'])
            self.disconnect()
        except IqTimeout:
            logging.error("No hubo respuesta del servidor")
            self.disconnect()


if __name__ == '__main__':

    inicio()
    x = input("Ingrese la opcion que desea realizar:\n")
    optp = OptionParser()

    # Opciones de output
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # Opciones de JID y password .
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")

    opts, args = optp.parse_args()

    # Setear el login
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    if opts.jid is None:
        opts.jid = input("Username: ")
    if opts.password is None:
        opts.password = getpass.getpass("Password: ")

    # Setup de mi clase EchoBot
    xmpp = EchoBot(opts.jid, opts.password, x)

    # plugins de registro
    xmpp.register_plugin('xep_0030')  # Service Discovery
    xmpp.register_plugin('xep_0004')  # Data forms
    xmpp.register_plugin('xep_0066')  # Out-of-band Data
    xmpp.register_plugin('xep_0077')  # In-band Registration
    xmpp['xep_0077'].force_registration = False

    # Conexion con el server
    if xmpp.connect():

        xmpp.process(block=False)
        print("Done")
        while (True):
            menu()
            menu_opcion = input("Ingrese la opcion que desea realizar: \n")

            # Nos da los contactos que tenemos que estan en linea
            if (menu_opcion == '1'):
                print("\nContacts:")
                y = xmpp.client_roster
                print(y.keys())
                print("")

            ##Mensaje a un usuario
            elif (menu_opcion == '2'):
                user = input("Usuario a quien desea enviar mensaje: ")
                message = input("Mensaje:")
                print("Enviando mensaje")
                xmpp.send_message(mto=user, mbody=message, mtype='chat')
                print("Su mensaje fue enviado exitosamente\n")

            ##Agregar usuario
            elif (menu_opcion == '3'):
                user = input("Ingrese el nombre del usuario que desea agregar: \n")
                xmpp.send_presence(pto=user, ptype='subscribe')

            ##Mensaje grupal
            elif (menu_opcion == '4'):
                print("")
                mensaje = input("Ingrese el mensaje que quiere enviar")




            ##Desconectarme
            elif (menu_opcion == '5'):
                print('Desconectandose')
                xmpp.disconnect()

                break

            ##Mostrar detalles de contacto
            elif (menu_opcion == '6'):
                x = input("Ingrese el contacto que desea buscar:")
                y = xmpp.client_roster
                print("Detalles de contacto de: " + x + "\n")
                print(y[x])


            ##Definir nuestro mensaje de preferencia
            elif (menu_opcion == '7'):

                x = input("Que mensaje e gustaria mostrar?: ")
                y = input("Cual es su mensaje de preferencia?: ")
                xmpp.makePresence(pfrom=xmpp.jid, pstatus=x, pshow=y)


            ##Eliminar mi cuenta
            elif (menu_opcion == '8'):
                yes = input("Esta seguro de que quiere eliminar su cuenta? (si/no)")

                if (yes == 'si'):
                    print("removing")
                    xmpp.delete()
                    xmpp.disconnect()

                else:
                    menu()
                    print("")
            ##regresar al menu principal
            elif (menu_opcion == '0'):
                print("")

            ##envioo de archivos
            elif (menu_opcion == '9'):
                persona = input("Ingrese el usuario a quien le quiere enviar el archivo: ")
                file = input("Ingrese el nombre del file: ")
                xmpp.send_file(file, persona)

    else:
        print("Unable to connect.")


