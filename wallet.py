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
    template_values = {'header': header.getHeader('/newAddress'), 'footer': header.getFooter()}

    # get amount to send and address to send to from the web form
    sendAmt = float(self.request.get('sendAmt'))
    sendAddr = self.request.get('sendAddr')

    # get user's current account balances
    query = Address.query().filter(Address.user == user)
    addresses = query.fetch()
    error = ''
    notif = ''
    if(sendAmt < 0):
      error = 'Cannot send a negative amount of bitcoin'
    elif(sendAmt + minefee > getBalance(addresses)):
      error = 'Cannot make the transaction because you do not have enough combined bitcoin associated with the addresses in your wallet. You requested to send ' + str(sendAmt) + ' BTC but you only have ' + str(getBalance(addresses)-minefee) + " BTC after a miner's fee of " + str(minefee) + ' is deducted.'
    else:
      list.sort(addresses)

      # figure out the user's addresses to use as inputs to the transaction
      uAddr = []
      ins = []
      keys = []
      changeAddr = None #?
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
          unspentOutputs = unspent(a.address)
          pq = Address.query().filter(Address.address == a.address)
          key = pq.fetch()[0].pk
          for u in unspentOutputs:
            ins.append(u)
            keys.append(key)
            logging.info(key)
          if currSend < 0:
            a.balance = -currSend
            currSend = 0
            changeAddr = a
          a.put()


      # it should work out so that outputs - inputs = minefee
      outs = [{'value': sendAmt / 0.00000001, 'address': sendAddr}]
      if(not changeAddr == None):
        outs.append({'value': changeAddr.balance / 0.00000001, 'address': changeAddr.address})
        # change is the change address and amount of change is how much is in that address
      tx = mktx(ins, outs)
      logging.info(keys)
      for i in xrange(len(keys)):
        tx = sign(tx, i, keys[i])
      logging.info(tx)
      pushtx(tx)
      notif = 'Transaction broadcasted to Bitcoin network. Please allow at least 30 minutes for the transaction to be finalized.'
      template_values['notif'] = notif
      template_values['sendAmt'] = sendAmt
      template_values['sendAddr'] = sendAddr
      template_values['usedAddresses'] = uAddr
      template_values['changeAddressObj'] = changeAddr

    template_values['error'] = error
    template = main.jinja_environment.get_template('sendBitcoin.html')
    self.response.out.write(template.render(template_values))

class UpdateHandler(webapp2.RequestHandler):
  def get(self):
    query = Address.query().filter(Address.user == users.get_current_user())
    addresses = query.fetch()
    updateUserBalances(addresses)
    self.redirect('/wallet')

class PaperHandler(webapp2.RequestHandler):
  def get(self):
    pass

class SettingsHandler(webapp2.RequestHandler):
  def get(self):
    pass

def generateAddress(user):
  query = Wallet.query().filter(Wallet.user == users.get_current_user())
  wallet = query.fetch()

#update the balance for a single address
def updateBalance(addr):
  balance = urllib.urlopen('https://blockchain.info/q/addressbalance/' + addr + '?confirmations=6').read()
  logging.info('https://blockchain.info/q/addressbalance' + addr + '?confirmations=6')
  balance = int(balance) * 0.00000001
  query = Address.query().filter(Address.address == addr)
  aObj = query.fetch()[0]
  aObj.balance = balance
  aObj.put()

def updateUserBalances(addresses):
  logging.info("updating balances")
  for a in addresses:
    updateBalance(a.address)

def getBalance(addresses):
  totalbal = 0
  for address in addresses:
    totalbal += address.balance
  return totalbal
