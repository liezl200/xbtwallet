from main import *
import main
from google.appengine.ext import ndb
from google.appengine.api import users
from bitcoin.transaction import *
from bitcoin.bci import *
import urllib

class Address(ndb.Model):
  address = ndb.StringProperty(required=True)
  pk = ndb.StringProperty(required=True)
  user = ndb.UserProperty(required=True)
  balance = ndb.FloatProperty(required=True)
  name = ndb.StringProperty()

class WalletHandler(webapp2.RequestHandler):
  def get(self):
    template_values = {'header': header.getHeader('/createItem'), 'footer': header.getFooter()}
    query = Address.query().filter(Address.user == users.get_current_user())
    addresses = query.fetch()
    totalbal = getBalance(addresses)
    template_values['addresses'] = addresses
    template_values['totalbal'] = totalbal
    template = main.jinja_environment.get_template('wallet.html')
    self.response.out.write(template.render(template_values))

    #get amount of Bitcoin
    #display public Bitcoin address
    #button to go to footer
    #generate new bitcoin address

class CreateAddressHandler(webapp2.RequestHandler):
  def get(self):
    name = self.request.get('name')
    user = users.get_current_user()
    #get a random bitcoin address + pk from blockchain.info API
    addresses = urllib.urlopen('https://blockchain.info/q/newkey').read()
    address = addresses[:addresses.find(' ')]
    pk = addresses[addresses.find(' ') + 1:]
    a = Address(address = address, pk = pk, user = user, balance = 0, name = name)
    a.put()
    template_values = {'header': header.getHeader('/newAddress'), 'footer': header.getFooter(), 'address': a}
    template = main.jinja_environment.get_template('createAddress.html')
    self.response.out.write(template.render(template_values))

class SendBitcoinHandler(webapp2.RequestHandler):
  def get(self):
    minefee = 0.0001
    user = users.get_current_user()

    # get amount to send and address to send to from the web form
    sendAmt = self.request.get('sendAmt')
    sendAddr = self.request.get('sendAddr')

    # get user's current account balances
    query = Address.query().filter(Address.user == user)
    addresses = query.fetch()
    error = ''
    notif = ''
    if(sendAmt + minefee > getBalance(addresses)):
      error = 'Cannot make the transaction because you do not have enough combined bitcoin associated with the addresses in your wallet. You requested to send ' + str(sendAmt) + ' BTC but you only have ' + str(getBalance(addresses)-minefee) + " BTC after a miner's fee of " + str(minefee) + ' is deducted.'
    else:
      sort(addresses)

      # figure out the user's addresses to use as inputs to the transaction
      uAddr = []
      changeAddr = null #?
      currSend = sendAmt + minefee
      for a in addresses:
        if currSend == 0:
          break
        elif currSend < 0:
          error = 'logic error'
        elif a.balance > 0:
          uAddr.append(a.address)
          currSend = currSend - a.balance
          a.balance = 0
          if currSend < 0:
            a.balance = -currSend
            currSend = 0
            changeAddr = a


      # it should work out so that outputs - inputs = minefee

      # figure out inputs
      ins = unspent(uAddr) #might have to unpack these addresses to use it as a parameter to the unspent function

      #figure out outputs (2)
      outs = [{'value': sendAmt, 'address': sendAddr.address}]
      if(not changeAddr == null):
        outs.append({'value': changeAddr.balance, 'address': changeAddr.address})
        # change is the change address and amount of change is how much is in that address
      tx = mktx(ins, outs)
      keys = []

      for inp in ins:
        pq = Address.query().filter(Address.address == inp)
        keys.append(pq.fetch()[0].pk)
      stx = signall(tx, keys)
      pushtx(stx)
      notif = 'Transaction broadcasted to Bitcoin network. Please allow at least 30 minutes for the transaction to be finalized.'

    template_values['notif'] = notif
    template_values['error'] = error

    template = main.jinja_environment.get_template('sendBTCtx.html')
    self.response.out.write(template.render(template_values))


class PaperHandler(webapp2.RequestHandler):
  def get(self):
    pass

class SettingsHandler(webapp2.RequestHandler):
  def get(self):
    pass

def generateAddress(user):
  query = Wallet.query().filter(Wallet.user == users.get_current_user())
  wallet = query.fetch()

def getBalance(addresses):
  totalbal = 0
  for address in addresses:
    totalbal += address.balance
  return totalbal
