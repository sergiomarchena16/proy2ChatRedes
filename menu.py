# proyecto 2 de redes
# chat con XMPP
# Sergio Marchena
# 16387

import blessed

term = blessed.Terminal()
isFirst = True

options = {
  '/dc': 'Disconect',
  '/list': 'List users',
  '/add': 'Add user to contacts - /add [contact]',
  '/peek': 'See details for user /peek [contact]',
  '/jc': 'Join Conversation /jc [contact]',
  '/jr': 'Join Room - /jr [room]',
  '/lr': 'Leave Room - /lr [message](optional)',
  '/cpm': 'Change presence message - /cpm [new-message]',
  '/sf': 'Send File - /sf [path-to-file] [file_reciever]',
  '/rm': 'Remove account from server',
  '/h': 'Help'
}


def showOptions(args=''):
  # Evaluate if its the fist showing of the menu or not
  j = term.location(0, int(term.height/2)) if isFirst else term.location()
  with j:
    print(term.center(term.blink('Commands')))
    # Iterate over options
    for key, value in options.items():
      print(term.bold(term.center(key + ': ' +value)))

def menu(functions):
  """ Show menu for the first time and update isFirst flag so that the menu
  knows further usages of showOptions are in a different term possition """
  showOptions()
  global isFirst
  isFirst = False
  functions['h'] = showOptions
  while True:
    # get input from user
    message = input(term.move(term.height - 1, 0) + ':')
    # see if it is a command. If not, send message to current conversation
    if message.startswith('/'):
      command = message.strip().split()[0][1:]
      # is in command list?
      if command in functions:
        arg = message[2 + len(command):]
        functions[command](arg)
      else:
        print(term.bold_red('Command ' + command + ' not found, please try again (/h for help on available commands)'))
    else:
      functions['send_message'](message)
