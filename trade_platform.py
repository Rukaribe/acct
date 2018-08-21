from acct import Accounts
from acct import Ledger
import pandas as pd
import argparse
import logging
import datetime
import urllib.request

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

class Trading(Ledger):
	def __init__(self, ledger, comm=0.0, sim=False, date=None):
		self.df = ledger.df
		self.ledger_name = ledger.ledger_name
		self.entity = ledger.entity
		self.date = ledger.date
		self.start_date = ledger.start_date
		self.txn = ledger.txn

		self.comm = comm
		if self.entity is not None:
			cur = ledger.conn.cursor()
			self.comm = cur.execute('SELECT comm FROM entities WHERE entity_id = ' + str(self.entity) + ';').fetchone()[0]
			cur.close()
		self.sim = sim
		self.date = date

	def get_price(self, symbol, date=None): # TODO Use global bool flag to get price from historical data for simulation trading
		if not self.sim:
			url = 'https://api.iextrading.com/1.0/stock/'
			try:
				price = float(urllib.request.urlopen(url + symbol + '/price').read())
			except:
				logging.warning('Error getting price from: ' + url + symbol + '/price\n')
				return 0
			else:
				return price
		else:
			infile = 'trading/market_data/quote/iex_quote_' + date + '.csv'
			try:
				with open(infile, 'r') as f:
					hist_df = pd.read_csv(f, index_col='symbol')
					price = float(hist_df.at[symbol.upper(),'close'])
					if pd.isnull(price):
						print('Price is blank for: '+ symbol + '\n')
						return 0
					return price
			except: # TODO Add error handling to get the most recent price
				logging.warning('Error getting historical price for: ' + symbol + '\n')
				return 0

	def trade_date(self, date=None):
		if date is None:
			date = datetime.datetime.today().strftime('%Y-%m-%d')
		return date

	def com(self): # If I want to add more logic to commissions calculation
		com = self.comm
		return com

	def buy_shares(self, symbol, qty=None, date=None):
		if qty == None:
			qty = int(input('How many shares? '))
		if self.sim:
			if date is None:
				date = input('Enter a date as format yyyy-mm-dd: ')
		price = self.get_price(symbol, date)

		# Check if there is enough capital
		capital_accts = ['Cash','Chequing']
		capital_bal = 0
		capital_bal = self.balance_sheet(capital_accts)

		if price * qty > capital_bal or price == 0:
			logging.info('Buying ' + str(qty) + ' shares of ' + symbol + ' costs $' + str(round(price * qty, 2)) + '.')
			logging.info('You currently have $' + str(round(capital_bal, 2)) + ' available.\n')
			return capital_bal

		# Journal entries for a buy transaction
		buy_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Shares buy', symbol, price, qty, 'Investments', 'Cash', price * qty]
		if self.com() != 0:
			com_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Comm. buy', '', '', '', 'Commission Expense', 'Cash', self.com()]
		if self.com() != 0:
			buy_event = [buy_entry, com_entry]
		else:
			buy_event = [buy_entry]

		self.journal_entry(buy_event)
		return capital_bal

	def sell_shares(self, symbol, qty=None, date=None):
		if qty is None:
			qty = int(input('How many shares? '))
		if self.sim:
			if date is None:
				date = input('Enter a date as format yyyy-mm-dd: ')
		current_qty = self.get_qty(symbol, 'Investments')
		if qty > current_qty:
			print('You currently have ' + str(round(current_qty, 2)) + ' shares of ' + symbol + ' but you tried to sell ' + str(round(qty, 2)) + ' shares.')
			return

		# Calculate profit
		price = self.get_price(symbol, date)
		if price == 0:
			return symbol
		sale_proceeds = qty * price
		hist_cost = self.hist_cost(qty, symbol, 'Investments')
		investment_gain = None
		investment_loss = None
		if sale_proceeds >= hist_cost:
			investment_gain = sale_proceeds - hist_cost
		else:
			investment_loss = hist_cost - sale_proceeds

		# Journal entries for a sell transaction
		sell_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Shares sell', symbol, hist_cost / qty, qty, 'Cash', 'Investments', hist_cost]
		if investment_gain is not None:
			profit_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Realized gain', '', price, '', 'Cash', 'Investment Gain', investment_gain]
		if investment_loss is not None:
			profit_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Realized loss', '', price, '', 'Investment Loss', 'Cash', investment_loss]
		if self.com() != 0:
			com_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Comm. sell', '', '', '','Commission Expense', 'Cash', self.com()]
		if self.com() != 0:
			sell_event = [sell_entry, profit_entry, com_entry]
		else:
			sell_event = [sell_entry, profit_entry]

		self.journal_entry(sell_event)

		# TODO Handle stock splits

	def int_exp(self, ledger, loan_accts=None, date=None): # TODO Add commenting
		if loan_accts is None:
			loan_accts = ['Credit Line','Student Credit'] # TODO Maybe generate list from liability accounts
		loan_bal = 0
		loan_bal = self.balance_sheet(loan_accts)
		if loan_bal < 0:
			logging.info('Loan exists!')
			cur = ledger.conn.cursor()
			for loan_type in loan_accts:
				loans = pd.unique(self.df.loc[self.df['credit_acct'] == loan_type]['item_id'])
				for loan in loans:
					try:
						debits = self.df.loc[self.df['item_id'] == loan].groupby('debit_acct').sum()['amount'][loan_type]
					except:
						debits = 0
					try:
						credits = self.df.loc[self.df['item_id'] == loan].groupby('credit_acct').sum()['amount'][loan_type]
					except:
						credits = 0
					loan_bal = credits - debits
					if loan_bal > 0:
						int_rate_fix = cur.execute('SELECT int_rate_fix FROM items WHERE item_id = "' + str(loan) + '";').fetchone()[0]
						logging.info('Int. Rate Fixed: {}'.format(int_rate_fix))
						int_rate_var = cur.execute('SELECT int_rate_var FROM items WHERE item_id = "' + str(loan) + '";').fetchone()[0]
						logging.info('Int. Rate Var.: {}'.format(int_rate_var))
						if int_rate_var is None:
							url = 'http://www.rbcroyalbank.com/rates/prime.html'
							rbc_prime_rate = pd.read_html(url)[5].iloc[1,1]
							try:
								int_rate_var = round(float(rbc_prime_rate) / 100, 4)
							except:
								logging.critical('RBC Rates Website structure has changed.')
								int_rate_var = 0
						logging.info('RBC Prime Rate: {}'.format(rbc_prime_rate))

					rate = int_rate_fix + int_rate_var
					period = 1 / 365 # TODO Add frequency logic
					int_amount = round(loan_bal * rate * period, 2)
					logging.info('Int. Expense: {}'.format(int_amount))
					int_exp_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Interest expense', '', '', '', 'Interest Expense', 'Cash', int_amount]
					int_exp_event = [int_exp_entry]
					self.journal_entry(int_exp_event)
			cur.close()

	def unrealized(self, date=None): # TODO Add commenting
		inv = self.get_qty(acct='Investments')
		if inv.empty:
			print('No securities held to true up.')
			return
		logging.debug('Inventory: \n{}'.format(inv))

		try:
			rvsl_txns = self.df[self.df['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
			if rvsl_txns.empty:
				print('First or second true up run.')
			logging.debug('RVSL TXNs: {}'.format(rvsl_txns))
			# Get list of txns
			inv_txns = self.df[( (self.df['debit_acct'] == 'Unrealized Loss') | (self.df['credit_acct'] == 'Unrealized Gain') ) & (~self.df['event_id'].isin(rvsl_txns))]
			logging.debug('Inv TXNs: {}'.format(inv_txns))
			for txn in inv_txns.iterrows():
				self.reversal_entry(str(txn[0]), date)
		except:
			logging.warning('Unrealized booking error.')

		for index, item in inv.iterrows():
			logging.debug(item.iloc[0])
			symbol = item.iloc[0]
			price = self.get_price(symbol, date)
			if price == 0:
				return symbol
			qty = item.iloc[1]
			market_value = qty * price
			hist_cost = self.hist_cost(qty, symbol, 'Investments')
			unrealized_gain = None
			unrealized_loss = None
			if market_value == hist_cost:
				logging.debug('No gains.')
				continue
			elif market_value > hist_cost:
				unrealized_gain = market_value - hist_cost
			else:
				unrealized_loss = hist_cost - market_value
			if unrealized_gain is not None:
				true_up_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Unrealized gain', symbol, price, '', 'Investments', 'Unrealized Gain', unrealized_gain ]
				logging.debug(true_up_entry)
			if unrealized_loss is not None:
				true_up_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Unrealized loss', symbol, price, '', 'Unrealized Loss', 'Investments', unrealized_loss ]
				logging.debug(true_up_entry)
			true_up_event = [ true_up_entry ]
			logging.info(true_up_event)

			self.journal_entry(true_up_event)

	def dividends(self, end_point='dividends/3m', date=None): # TODO Add commenting
		url = 'https://api.iextrading.com/1.0/stock/'
		portfolio = self.get_qty()
		if portfolio.empty:
			print('Dividends: No securities held.')
			return
		logging.debug('Looking for dividends to book.')
		logging.debug(portfolio['item_id'])
		for symbol in portfolio['item_id']:
			logging.debug('\nGetting divs for: ' + symbol)
			try:
				div = pd.read_json(url + symbol + '/' + end_point, typ='frame', orient='records')
				if div.empty:
					continue
			except:
				logging.warning('Invalid ticker: ' + symbol)
				logging.debug(url + symbol + '/' + end_point)
				continue
			exdate = div.iloc[0,2]
			if exdate is None:
				logging.warning('Exdate is blank for: ' + symbol)
				continue
			exdate = datetime.datetime.strptime(exdate, '%Y-%m-%d')
			current_date = datetime.datetime.today().strftime('%Y-%m-%d')
			logging.debug('Exdate: {}'.format(exdate))
			logging.debug('Current Date: {}'.format(current_date))
			if current_date == exdate:
				div_rate = div.iloc[0,0]
				if div_rate is None:
					logging.warning('Div rate is blank for: ' + symbol)
					continue
				qty = self.get_qty(symbol, 'Investments')
				try:
					div_proceeds = div_rate * qty
				except:
					logging.warning('Div proceeds is blank for: ' + symbol)
					continue
				logging.debug('QTY: {}'.format(qty))
				logging.debug('Div Rate: {}'.format(div.iloc[0,0]))
				logging.debug('Div Proceeds: {}'.format(div_proceeds))
				div_accr_entry = [self.get_event(), self.get_entity(), self.trade_date(date), 'Dividend income accrual', symbol, div_rate, qty, 'Dividend Receivable', 'Dividend Income', div_proceeds]
				div_accr_event = [div_accr_entry]
				print(div_accr_event)
				self.journal_entry(div_accr_event)

	def div_accr(self, end_point='dividends/3m', date=None): # TODO Add commenting
		url = 'https://api.iextrading.com/1.0/stock/'
		rvsl_txns = self.df[self.df['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		div_accr_txns = self.df[( self.df['debit_acct'] == 'Dividend Receivable') & (~self.df['event_id'].isin(rvsl_txns))] # Get list of div accrual entries
		logging.debug(div_accr_txns)
		for index, div_accr_txn in div_accr_txns.iterrows():
			logging.debug(div_accr_txn)
			symbol = str(div_accr_txn[4])
			logging.debug('Getting divs for ' + symbol)
			try:
				div = pd.read_json(url + symbol + '/' + end_point, typ='frame', orient='records')
				logging.debug(div)
				if div.empty:
					continue
			except:
				logging.warning('Invalid ticker: ' + symbol)
				logging.debug(url + symbol + '/' + end_point)
				continue
			paydate = div.iloc[0,5]
			if paydate is None:
				logging.warning('Paydate is blank for: ' + symbol)
				continue
			paydate = datetime.datetime.strptime(paydate, '%Y-%m-%d')
			current_date = datetime.datetime.today().strftime('%Y-%m-%d')
			logging.debug('Paydate: {}'.format(paydate))
			logging.debug('Current Date: {}'.format(current_date))
			if current_date == paydate:
				div_relieve_entry = [div_accr_txn.iloc[0], div_accr_txn.iloc[1], self.trade_date(date), 'Dividend income payment', symbol, div_accr_txn.iloc[5], div_accr_txn.iloc[6], 'Cash', 'Dividend Receivable', div_accr_txn.iloc[9]]
				div_relieve_event = [div_relieve_entry]
				print(div_relieve_event)
				self.journal_entry(div_relieve_event)

	def splits(self, end_point='splits/3m', date=None): # TODO Add commenting
		url = 'https://api.iextrading.com/1.0/stock/'
		portfolio = self.get_qty()
		if portfolio.empty:
			print('Stock Splits: No securities held.')
			return
		logging.debug('Looking for stock splits to book.')
		for symbol in portfolio['item_id']:
			logging.debug('\nGetting splits for ' + symbol)
			try:
				split = pd.read_json(url + symbol + '/' + end_point, typ='frame', orient='records')
				if split.empty:
					continue
			except:
				logging.warning('Invalid ticker: ' + symbol)
				logging.debug(url + symbol + '/' + end_point)
				continue
			exdate = split.iloc[0,1]
			if exdate is None:
				logging.warning('Exdate is blank for: ' + symbol)
				continue
			exdate = datetime.datetime.strptime(exdate, '%Y-%m-%d')
			current_date = datetime.datetime.today().strftime('%Y-%m-%d')
			logging.debug('Exdate: {}'.format(exdate))
			logging.debug('Current Date: {}'.format(current_date))
			if current_date == exdate:
				to_factor = split.iloc[0,6]
				for_factor = split.iloc[0,2]
				ratio = to_factor / for_factor
				qty = self.get_qty(symbol)
				cost = self.hist_cost(qty, symbol, 'Investments')
				old_price = cost / qty
				new_qty = qty * ratio # TODO Handle fractional shares
				new_price = cost / new_qty

				logging.debug('To Factor: {}'.format(to_factor))
				logging.debug('For Factor: {}'.format(for_factor))
				logging.debug('Ratio: {}'.format(ratio))
				logging.debug('Ticker: {}'.format(symbol))
				logging.debug('QTY: {}'.format(qty))
				logging.debug('Cost: {}'.format(cost))
				logging.debug('Old Price: {}'.format(old_price))
				logging.debug('New QTY: {}'.format(new_qty))
				logging.debug('New Price: {}'.format(new_price))

				cost_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Stock split old', symbol, old_price, qty, 'Cash', 'Investments', cost]
				split_entry = [ self.get_event(), self.get_entity(), self.trade_date(date), 'Stock split new', symbol, new_price, new_qty, 'Investments', 'Cash', cost]
				split_event = [cost_entry, split_entry]
				print(split_event)
				self.journal_entry(split_event)


if __name__ == '__main__':
	# TODO Add argparse to make trades
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	parser.add_argument('-sim', '--simulation', action='store_true', help='Run on historical data.')
	args = parser.parse_args()

	accts = Accounts(conn=args.database)
	ledger = Ledger(ledger_name=args.ledger,entity=args.entity)
	trade = Trading(ledger, sim=args.simulation)

	while True:
		command = input('\nType one of the following commands:\nbuy, sell, exit\n')
		if command.lower() == 'exit':
			exit()
		# TODO Allow command to be a single line in any order (i.e. buy tsla 10)
		elif command.lower() == 'buy':
			symbol = input('Which ticker? ')
			trade.buy_shares(symbol)
		elif command.lower() == 'sell':
			symbol = input('Which ticker? ')
			trade.sell_shares(symbol)
		else:
			print('Not a valid command. Type exit to close.')