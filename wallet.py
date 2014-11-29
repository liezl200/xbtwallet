from main import *
from google.appengine.ext import ndb
from google.appengine.api import users
from bitcoin.transaction import *
import urllib

class Address(ndb.Model):
  address = ndb.StringProperty(required=True)
  pk = ndb.StringProperty(required=True)
  user = ndb.UserProperty(required=True)
  balance = ndb.FloatProperty(required=True)
  name = ndb.StringProperty()

class WalletHandler(webapp2.RequestHandler):
	def get(self):
		template_values = {"header": header.getHeader('/createItem'), "footer": header.getFooter()}
		query = Address.query().filter(Address.user == users.get_current_user())
		addresses = query.fetch()
		totalbal = getBalance(addresses)
		template_values["addresses"] = addresses
		template_values["totalbal"] = totalbal
 		template = jinja_environment.get_template("wallet.html")

		#get amount of Bitcoin
		#display public Bitcoin address
		#button to go to footer
		#generate new bitcoin address

class CreateAddressHandler(webapp2.RequestHandler):
	def get(self):
		name = self.request.get('name')
		user = users.get_current_user()
		#get a random bitcoin address + pk from blockchain.info API
		addresses = urllib.urlopen("https://blockchain.info/q/newkey").read()
		address = addresses[:addresses.find(" ")]
		pk = addresses[addresses.find(" ") + 1:]
		a = Address(address = address, pk = pk, user = user, balance = 0, name = name)
		a.put()
    template_values = {"header": header.getHeader('/newAddress'), "footer": header.getFooter(), "address": a}
    template = jinja_environment.get_template('createAddress.html')
    self.response.out.write(template.render(template_values))

class SendBitcoinHandler(webapp2.RequestHandler):
	def get(self):
		user = users.get_current_user()
		sendAmt = self.request.get('sendAmt')
		query = Address.query().filter(Address.user == users.get_current_user())
		addresses = query.fetch()
		error = ""
		if(sendAmt > getBalance(addresses) - 0.0001):
			error = "Cannot make the transaction because you do not have enough combined bitcoin associated with the addresses in your wallet. You requested to send " + str(sendAmt) + " BTC but you only have " + str(getBalance(addresses)-0.0001) + " BTC after a miner's fee of 0.0001 is subtracted."
		else:
			# create transaction, sign it, and broadcast it to the Bitcoin network
			u = unspent(addresses) #might have to unpack these addresses to use it as a parameter to the unspent function
		template_values['error'] = error


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
