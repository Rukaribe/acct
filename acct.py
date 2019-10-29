import pandas as pd
import numpy as np
import sqlite3
import argparse
import datetime
import logging
import warnings
import time
# from contextlib import contextmanager


DISPLAY_WIDTH = 98
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', 30)
pd.options.display.float_format = '${:,.2f}'.format
logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%b-%d %I:%M:%S %p', level=logging.WARNING) #filename='logs/output.log'

class Accounts:
	def __init__(self, conn=None, standard_accts=None, entities_table_name=None, items_table_name=None):
		if conn is None:
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/acct.db')
				self.website = True
				logging.debug('Website: {}'.format(self.website))
			except:
				conn = sqlite3.connect('db/acct.db')
				self.website = False
				logging.debug('Website: {}'.format(self.website))
			self.db = 'acct.db'
		elif isinstance(conn, str):
			self.db = conn
			if '/' not in conn:
				conn = 'db/' + conn
			try:
				conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/' + conn)
				self.website = True
				logging.debug('Website: {}'.format(self.website))
			except:
				conn = sqlite3.connect(conn)
				self.website = False
				logging.debug('Website: {}'.format(self.website))
		# else:
		# 	print('Conn path: {}'.format(conn))
		# 	try:
		# 		conn = sqlite3.connect('/home/robale5/becauseinterfaces.com/acct/db/acct.db')
		# 		self.website = True
		# 		logging.debug('Website: {}'.format(self.website))
		# 	except:
		# 		conn = sqlite3.connect('db/acct.db')
		# 		self.website = False
		# 		logging.debug('Website: {}'.format(self.website))

		# self.db = args.database
		self.conn = conn

		try:
			self.refresh_accts()
			if entities_table_name is None:
				self.entities_table_name = 'entities'
			else:
				self.entities_table_name = entities_table_name
			if items_table_name is None:
				self.items_table_name = 'items'
			else:
				self.items_table_name = items_table_name
		except:
			self.coa = None
			self.create_accts(standard_accts)
			# self.refresh_accts()
			if entities_table_name is None:
				self.entities_table_name = 'entities'
			else:
				self.entities_table_name = entities_table_name
			self.create_entities()
			if items_table_name is None:
				self.items_table_name = 'items'
			else:
				self.items_table_name = items_table_name
			self.create_items()

	def create_accts(self, standard_accts=None):
		if standard_accts is None:
			standard_accts = []
		create_accts_query = '''
			CREATE TABLE IF NOT EXISTS accounts (
				accounts text,
				child_of text
			);
			'''
		base_accts = [
			('Account','None'),
			('Admin','Account'),
			('Asset','Account'),
			('Liability','Account'),
			('Equity','Account'),
			('Revenue','Equity'),
			('Expense','Equity'),
			('Transfer','Equity')
		]

		personal = [
			('Cash','Asset'),
			('Chequing','Asset'),
			('Savings','Asset'),
			('Investments','Asset'),
			('Visa','Liability'),
			('Student Credit','Liability'),
			('Credit Line','Liability'),
			('Uncategorized','Admin'),
			('Info','Admin'),
			('Royal Credit Line','Liability')
		]

		base_accts = base_accts + standard_accts + personal

		cur = self.conn.cursor()
		cur.execute(create_accts_query)
		self.conn.commit()
		cur.close()
		self.add_acct(base_accts)

	# TODO Maybe make entities a class
	def create_entities(self): # TODO Add command to book more entities
		create_entities_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.entities_table_name + ''' (
				entity_id INTEGER PRIMARY KEY,
				name text,
				comm real DEFAULT 0,
				min_qty INTEGER,
				max_qty INTEGER,
				liquidate_chance real,
				ticker_source text DEFAULT 'iex',
				entity_type text,
				government text,
				hours INTEGER,
				needs text,
				need_max INTEGER DEFAULT 100,
				decay_rate INTEGER DEFAULT 1,
				need_threshold INTEGER DEFAULT 40,
				current_need INTEGER DEFAULT 50,
				parents text,
				user text,
				auth_shares INTEGER,
				int_rate real,
				outputs text
			);
			''' # TODO Add needs table?
		default_entities = ['''
			INSERT INTO ''' + self.entities_table_name + ''' (
				name,
				comm,
				min_qty,
				max_qty,
				liquidate_chance,
				ticker_source,
				entity_type,
				government,
				hours,
				needs,
				need_max,
				decay_rate,
				need_threshold,
				current_need,
				parents,
				user,
				auth_shares,
				int_rate,
				outputs
				)
				VALUES (
					'Person001',
					0.0,
					1,
					100,
					0.5,
					'iex',
					'Individual',
					1,
					24,
					'Hunger',
					100,
					1,
					40,
					50,
					'(None,None)',
					'True',
					1000000,
					0.0,
					'Labour'
				);
			'''] # TODO Rename outputs to produces

		cur = self.conn.cursor()
		cur.execute(create_entities_query)
		for entity in default_entities:
				print('Entities table created.')
				cur.execute(entity)
		self.conn.commit()
		cur.close()

	# Maybe make items a class
	def create_items(self):# TODO Add command to book more items
		create_items_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.items_table_name + ''' (
				item_id text PRIMARY KEY,
				int_rate_fix real,
				int_rate_var real,
				freq integer DEFAULT 365,
				child_of text,
				requirements text,
				amount text,
				capacity integer,
				usage_req text,
				use_amount text,
				satisfies text,
				satisfy_rate text,
				productivity text,
				efficiency text,
				lifespan text,
				metric text DEFAULT 'ticks',
				dmg_type text,
				dmg text,
				res_type text,
				res text,
				byproduct text,
				byproduct_amt text,
				producer text
			);
			''' # Metric can have values of 'ticks' or 'units' or 'spoilage'
		default_item = ['''
			INSERT INTO ''' + self.items_table_name + ''' (
				item_id,
				int_rate_fix,
				int_rate_var,
				freq,
				child_of,
				requirements,
				amount,
				capacity,
				usage_req,
				use_amount,
				satisfies,
				satisfy_rate,
				productivity,
				efficiency,
				lifespan,
				metric,
				dmg_type,
				dmg,
				res_type,
				res,
				byproduct,
				byproduct_amt,
				producer
				) VALUES (
					'credit_line_01',
					0.0409,
					NULL,
					365,
					'loan',
					'Bank',
					'1',
					NULL,
					NULL,
					NULL,
					'Capital',
					1,
					NULL,
					NULL,
					3650,
					'ticks',
					NULL,
					NULL,
					NULL,
					NULL,
					NULL,
					NULL,
					'Bank'
				);
			''']

		cur = self.conn.cursor()
		cur.execute(create_items_query)
		for item in default_item:
				print('Items table created.')
				cur.execute(item)
		self.conn.commit()
		cur.close()

	def refresh_accts(self):
		self.coa = pd.read_sql_query('SELECT * FROM accounts;', self.conn, index_col='accounts')
		return self.coa

	def print_accts(self):
		self.refresh_accts()
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.coa)
		print('-' * DISPLAY_WIDTH)
		return self.coa

	def drop_dupe_accts(self):
		self.coa = self.coa[~self.coa.index.duplicated(keep='first')]
		self.coa.to_sql('accounts', self.conn, if_exists='replace')
		self.refresh_accts()

	def add_acct(self, acct_data=None, v=False):
		cur = self.conn.cursor()
		if acct_data is None:
			account = input('Enter the account name: ')
			child_of = input('Enter the parent account: ')
			if child_of not in self.coa.index:
				print('\n' + child_of + ' is not a valid account.')
				return
			details = (account, child_of)
			cur.execute('INSERT INTO accounts VALUES (?,?)', details)
		else:
			for acct in acct_data: # TODO Turn this into a list comprehension
				account = str(acct[0])
				child_of = str(acct[1])
				if v: print(acct)
				details = (account,child_of)
				cur.execute('INSERT INTO accounts VALUES (?,?)', details)
		self.conn.commit()
		cur.close()
		self.refresh_accts()
		self.drop_dupe_accts()

	def add_entity(self, entity_data=None): # TODO Cleanup and make nicer
		cur = self.conn.cursor()
		if entity_data is None:
			name = input('Enter the entity name: ')
			comm = input('Enter the commission amount: ')
			min_qty = '' # TODO Remove parameters related to random algo
			max_qty = ''
			liquidate_chance = ''
			ticker_source = input('Enter the source for tickers: ')
			entity_type = input('Enter the type of the entity: ')
			government = input('Enter the ID for the government the entity belongs to: ')
			hours = input('Enter the number of hours in a work day: ')
			needs = input('Enter the needs of the entity as a list: ')
			need_max = input('Enter the maximum need value as a list: ')
			decay_rate = input('Enter the rates of decay per day for each need.') # TODO Add int validation
			need_threshold = input('Enter the threshold for the needs as a list: ')
			current_need = input('Enter the starting level for the needs as a list: ')
			parents = input('Enter two IDs for parents as a tuple: ')
			user = input('Enter whether the entity is a user as True or False: ')
			auth_shares = input('Enter the number of shares authorized: ')
			int_rate = input('Enter the interest rate for the bank: ')
			outputs = input('Enter the output names as a list: ') # For corporations

			details = (name,comm,min_qty,max_qty,liquidate_chance,ticker_source,entity_type,government,hours,needs,need_max,decay_rate,need_threshold,current_need,parents,user,auth_shares,int_rate,outputs)
			cur.execute('INSERT INTO ' + self.entities_table_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', details)
			
		else:
			for entity in entity_data:
				entity = tuple(map(lambda x: np.nan if x == 'None' else x, entity))
				insert_sql = 'INSERT INTO ' + self.entities_table_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
				cur.execute(insert_sql, entity)

		self.conn.commit()
		entity_id = cur.lastrowid
		cur.close()
		return entity_id

	def add_item(self, item_data=None): # TODO Cleanup and make nicer
		cur = self.conn.cursor()
		if item_data is None:
			item_id = input('Enter the item name: ')
			int_rate_fix = ''#input('Enter the fixed interest rate if there is one: ')
			int_rate_var = ''#input('Enter the variable interest rate or leave blank: ')
			freq = ''#int(input('Enter the frequency of interest payments: '))
			child_of = input('Enter the category the item belongs to: ')
			# if child_of not in self.coa.index: # TODO Ensure item always points to an existing item
			# 	print('\n' + child_of + ' is not a valid account.')
			# 	return
			requirements = input('Enter the requirments to produce the item as a list: ')
			amount = input('Enter a value for the amount of each requirement as a list: ')
			capacity = input('Enter the capacity amount if there is one: ')
			usage_req = input('Enter the requirements to use the item as a list: ')
			use_amount = input('Enter a value for the amount of each requirement to use the item as list: ')
			satisfies = input('Enter the needs the item satisfies as a list: ')
			satisfy_rate = input('Enter the rate the item satisfies the needs as a list: ')
			productivity = input('Enter the requirements the item makes more efficient as a list: ')
			efficiency = input('Enter the ratio that the requirement is reduced by as a list: ')
			metric = input('Enter either "ticks" or "units" for how the lifespan is measured: ')
			lifespan = input('Enter how long the item lasts: ')
			dmg_types = input('Enter the types of damage (if any) the item can inflict as a list: ')
			dmg = input('Enter the amounts of damage (if any) the item can inflict as a list: ')
			res_types = input('Enter the types of damage resilience (if any) the item has as a list: ')
			res = input('Enter the amounts of damage resilience (if any) the item has as a list: ')
			byproduct = input('Enter the byproducts created (if any) when this item is produced as a list: ')
			byproduct_amt = input('Enter the amount of byproducts created (if any) when this item is produced as a list: ')
			producer = input('Enter the producer of the item: ')

			details = (item_id,int_rate_fix,int_rate_var,freq,child_of,requirements,amount,capacity,usage_req,use_amount,satisfies,satisfy_rate,productivity,efficiency,lifespan,metric,dmg_types,dmg,res_types,res,byproduct,byproduct_amt,producer)
			cur.execute('INSERT INTO ' + self.items_table_name + ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)', details)
			
		else:
			for item in item_data:
				item = tuple(map(lambda x: np.nan if x == 'None' else x, item))
				insert_sql = 'INSERT INTO ' + self.items_table_name + ' VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)'
				cur.execute(insert_sql, item)

		self.conn.commit()
		cur.close()

	def load_csv(self, infile=None):
		if infile is None:
			infile = input('Enter a filename: ')
		try:
			with open(infile, 'r') as f:
				load_csv = pd.read_csv(f, keep_default_na=False, comment='#')
			lol = load_csv.values.tolist()
		except Exception as e:
			print('Error: {}'.format(e))
		#print(load_csv)
		#print('-' * DISPLAY_WIDTH)
		return lol

	def load_accts(self, infile=None):
		self.add_acct(self.load_csv(infile), v=True)

	def load_entities(self, infile=None):
		if infile is None:
			infile = 'data/entities.csv'
		self.add_entity(self.load_csv(infile))
		self.entities = pd.read_sql_query('SELECT * FROM ' + self.entities_table_name + ';', self.conn, index_col='entity_id')
		return self.entities

	def load_items(self, infile=None):
		if infile is None:
			infile = 'data/items.csv'
		self.add_item(self.load_csv(infile))
		self.items = pd.read_sql_query('SELECT * FROM ' + self.items_table_name + ';', self.conn, index_col='item_id')
		return self.items

	def export_accts(self):
		outfile = 'accounts_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
		save_location = 'data/'
		try:
			self.coa.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=True)
			print('File saved as ' + save_location + outfile + '\n')
		except Exception as e:
			print('Error: {}'.format(e))

	def remove_acct(self, acct=None):
		if acct is None:
			acct = input('Which account would you like to remove? ')
		cur = self.conn.cursor()
		cur.execute('DELETE FROM accounts WHERE accounts=?', (acct,))
		self.conn.commit()
		cur.close()
		self.refresh_accts()

	def get_entities(self, entities_table_name=None):
		if entities_table_name is None:
			entities_table_name = self.entities_table_name
		self.entities = pd.read_sql_query('SELECT * FROM ' + entities_table_name + ';', self.conn, index_col=['entity_id'])
		return self.entities

	def get_items(self, items_table_name=None):
		if items_table_name is None:
			items_table_name=self.items_table_name
		self.items = pd.read_sql_query('SELECT * FROM ' + items_table_name + ';', self.conn, index_col=['item_id'])
		return self.items

	def print_entities(self, save=True): # TODO Add error checking if no entities exist
		#self.entities = pd.read_sql_query('SELECT * FROM ' + self.entities_table_name + ';', self.conn, index_col=['entity_id'])
		self.entities = self.get_entities()
		if save:
			self.entities.to_csv('data/entities.csv', index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.entities)
		print('-' * DISPLAY_WIDTH)
		return self.entities

	def print_items(self, save=True): # TODO Add error checking if no items exist
		#self.items = pd.read_sql_query('SELECT * FROM items;', self.conn, index_col=['item_id'])
		self.items = get_items()
		if save:
			self.items.to_csv('data/items.csv', index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.items)
		print('-' * DISPLAY_WIDTH)
		return self.items

	def print_table(self, table_name=None):
		if table_name is None:
			table_name = input('Enter a table to display: ')
		try:
			table = pd.read_sql_query('SELECT * FROM ' + table_name + ';', self.conn)
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print('{} table: \n{}'.format(table_name, table))
		except Exception as e:
			print('There exists no table called: {}'.format(table_name))
			print('Error: {}'.format(repr(e)))
			table = table_name
		return table

	def export_table(self, table_name=None):
		if table_name is None:
			table_name = input('Enter a table to export: ')
		try:
			table = pd.read_sql_query('SELECT * FROM ' + table_name + ';', self.conn)
			save_location = 'data/'
			outfile = table_name + datetime.datetime.today().strftime('_%Y-%m-%d_%H-%M-%S') + '.csv'
			table.to_csv(save_location + outfile, date_format='%Y-%m-%d', index=True)
			print('{} data saved to: {}'.format(table_name, save_location + outfile))
			# with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			# 	print('{} table export: \n{}'.format(table_name, table))
		except Exception as e:
			print('There exists no table called: {}'.format(table_name))
			print('Error: {}'.format(repr(e)))
			table = table_name
		return table


class Ledger:
	def __init__(self, accts, ledger_name=None, entity=None, date=None, start_date=None, txn=None, start_txn=None):
		self.conn = accts.conn
		self.coa = accts.coa
		if ledger_name is None:
			self.ledger_name = 'gen_ledger'
		else:
			self.ledger_name = ledger_name
		if entity is not None:
			if not isinstance(entity, (list, tuple)):
				if isinstance(entity, str):
					if ',' in entity:
						entity = [x.strip() for x in entity.split(',')]
						entity = list(map(int, entity))
					else:
						entity = [int(entity)]
				else:
					entity = [entity]
		self.entity = entity
		self.date = date
		self.start_date = start_date
		self.txn = txn
		self.start_txn = start_txn
		self.default = None
		self.create_ledger()
		self.refresh_ledger() # TODO Maybe make this self.gl = self.refresh_ledger()
		self.balance_sheet()
			
	def create_ledger(self): # TODO Change entity_id to string type maybe
		create_ledger_query = '''
			CREATE TABLE IF NOT EXISTS ''' + self.ledger_name + ''' (
				txn_id INTEGER PRIMARY KEY,
				event_id integer NOT NULL,
				entity_id integer NOT NULL,
				cp_id integer NOT NULL,
				date date NOT NULL,
				location text,
				description text,
				item_id text,
				price real,
				qty integer,
				debit_acct text,
				credit_acct text,
				amount real NOT NULL
			);
			'''

		cur = self.conn.cursor()
		cur.execute(create_ledger_query)
		self.conn.commit()
		cur.close()

	# @contextmanager
	def set_entity(self, entity=None):
		if entity is None:
			self.entity = input('Enter an Entity ID: ')
			if self.entity == '':
				self.entity = None
		else:
			self.entity = entity
		if self.entity is not None:
			if not isinstance(self.entity, (list, tuple)):
				if isinstance(self.entity, str):
					if ',' in self.entity:
						self.entity = [x.strip() for x in self.entity.split(',')]
						self.entity = list(map(int, self.entity))
					else:
						self.entity = [int(self.entity)]
				else:
					self.entity = [self.entity]
		self.refresh_ledger()
		self.balance_sheet()
		return self.entity
		# yield self.entity
		# self.reset()

	def set_date(self, date=None):
		if date is None:
			self.date = input('Enter a date in format YYYY-MM-DD: ')
		else:
			self.date = date
		try:
			datetime.datetime.strptime(self.date, '%Y-%m-%d')
		except ValueError:
			raise ValueError('Incorrect data format, should be YYYY-MM-DD.')
		self.refresh_ledger()
		self.balance_sheet()
		return self.date

	def set_start_date(self, start_date=None):
		if start_date is None:
			self.start_date = input('Enter a start date in format YYYY-MM-DD: ')
		else:
			self.start_date = start_date
		try:
			datetime.datetime.strptime(self.start_date, '%Y-%m-%d')
		except ValueError:
			raise ValueError('Incorrect data format, should be YYYY-MM-DD.')
		self.refresh_ledger()
		self.balance_sheet()
		return self.start_date

	def set_txn(self, txn=None):
		if txn is None:
			self.txn = int(input('Enter a TXN ID: '))
		else:
			self.txn = txn
		self.refresh_ledger()
		self.balance_sheet()
		return self.txn

	def set_start_txn(self, start_txn=None):
		if start_txn is None:
			self.start_txn = int(input('Enter a start TXN ID: '))
		else:
			self.start_txn = start_txn
		self.refresh_ledger()
		self.balance_sheet()
		return self.start_txn

	def reset(self):#, default=self.default):
		self.entity = self.default
		self.date = None
		self.start_date = None
		self.txn = None
		self.start_txn = None
		self.refresh_ledger()
		self.balance_sheet() # TODO This makes things very inefficient

	def refresh_ledger(self):
		# print('Refreshing Ledger.')
		self.gl = pd.read_sql_query('SELECT * FROM ' + self.ledger_name + ';', self.conn, index_col='txn_id')
		if self.entity is not None:
			self.gl = self.gl[(self.gl.entity_id.isin(self.entity))]
		if self.date is not None:
			self.gl = self.gl[(self.gl.date <= self.date)]
		if self.start_date is not None:
			self.gl = self.gl[(self.gl.date >= self.start_date)]
		if self.txn is not None:
			self.gl = self.gl[(self.gl.index <= self.txn)]
		if self.start_txn is not None:
			self.gl = self.gl[(self.gl.index >= self.start_txn)] # TODO Add event range
		return self.gl

	def print_gl(self):
		self.refresh_ledger() # Refresh Ledger
		display_gl = self.gl
		display_gl['qty'].replace(np.nan, '', inplace=True)
		display_gl['price'].replace(np.nan, '', inplace=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None): # To display all the rows
			print(display_gl)
		print('-' * DISPLAY_WIDTH)
		return self.gl

	def get_acct_elem(self, acct):
		if acct in ['Asset','Liability','Equity','Revenue','Expense','None']:
			return acct
		else:
			return self.get_acct_elem(self.coa.loc[acct, 'child_of'])

	def balance(self, accounts=None, item=None, nav=False, v=False):
		if accounts == '':
			accounts = None
		if item is not None: # TODO Add support for multiple items maybe
			if v: print('Item: \n{}'.format(item))
			self.gl = self.gl[self.gl['item_id'] == item]
		if accounts is None: # Create a list of all the accounts
			accounts = np.unique(self.gl[['debit_acct', 'credit_acct']].values).tolist()
		else:
			if not isinstance(accounts, (list, tuple)):
				accounts = [x.strip() for x in accounts.split(',')]
		if v: print('Accounts: \n{}'.format(accounts))
		self.gl = self.gl.loc[(self.gl['debit_acct'].isin(accounts)) | (self.gl['credit_acct'].isin(accounts))]
		if v: print('GL Filtered: \n{}'.format(self.gl))

		# TODO Modify tmp gl instead of self.gl
		self.gl['debit_acct_type'] = self.gl.apply(lambda x: self.get_acct_elem(x['debit_acct']), axis=1)
		self.gl['credit_acct_type'] = self.gl.apply(lambda x: self.get_acct_elem(x['credit_acct']), axis=1)
		self.gl['debit_amount'] = self.gl.apply(lambda x: x['amount'] if (x['debit_acct_type'] == 'Asset') | (x['debit_acct_type'] == 'Expense') else x['amount'] * -1, axis=1)
		self.gl['credit_amount'] = self.gl.apply(lambda x: x['amount'] * -1 if (x['credit_acct_type'] == 'Asset') | (x['credit_acct_type'] == 'Expense') else x['amount'], axis=1)
		if v: print('GL Enhanced: \n{}'.format(self.gl))

		debits = self.gl.groupby(['debit_acct','debit_acct_type']).sum()['debit_amount']
		debits.index.rename('acct', level=0, inplace=True)
		debits.index.rename('acct_type', level=1, inplace=True)
		if v: print('\nDebits: \n{}'.format(debits))
		credits = self.gl.groupby(['credit_acct','credit_acct_type']).sum()['credit_amount']
		credits.index.rename('acct', level=0, inplace=True)
		credits.index.rename('acct_type', level=1, inplace=True)
		if v: print('\nCredits: \n{}'.format(credits))
		bal = debits.add(credits, fill_value=0).reset_index()
		# if v: print('Add: \n{}'.format(bal))
		# bal = bal.reset_index()
		if v: print('Add Reset: \n{}'.format(bal))
		bal = bal.loc[(bal['acct'].isin(accounts))]
		if bal.empty:
			bal = 0
			return bal
		bal = bal.groupby(['acct_type']).sum()
		if v: print('New Bal: \n{}'.format(bal))
		try:
			asset_bal = bal.loc['Asset', 0]
		except KeyError as e:
			asset_bal = 0
		try:
			liab_bal = bal.loc['Liability', 0]
		except KeyError as e:
			liab_bal = 0
		try:
			equity_bal = bal.loc['Equity', 0]
		except KeyError as e:
			equity_bal = 0
		try:
			rev_bal = bal.loc['Revenue', 0]
		except KeyError as e:
			rev_bal = 0
		try:
			exp_bal = bal.loc['Expense', 0]
		except KeyError as e:
			exp_bal = 0
		retained_earnings = rev_bal - exp_bal
		net_asset_value = asset_bal - liab_bal
		if net_asset_value == 0: # Two ways to calc NAV depending on accounts
			net_asset_value = equity_bal + retained_earnings
		if v: print('NAV: \n{}'.format(net_asset_value))
		self.refresh_ledger()
		return net_asset_value # TODO This func is slow

#Option 1 (will be below):
# Asset  - Debit  bal - Pos : Dr. = pos & Cr. = neg
# Liab   - Credit bal - Neg : Dr. = pos & Cr. = neg
# =
# Equity - Credit bal - Pos : Dr. = neg & Cr. = pos
# Rev    - Credit bal - Pos : Dr. = neg & Cr. = pos
# Exp    - Debit  bal - Neg : Dr. = neg & Cr. = pos

#Option 2 (above):
# Asset  - Debit  bal - Pos : Dr. = pos & Cr. = neg
# Liab   - Credit bal - Pos : Dr. = neg & Cr. = pos
# =
# Equity - Credit bal - Pos : Dr. = neg & Cr. = pos
# Rev    - Credit bal - Pos : Dr. = neg & Cr. = pos
# Exp    - Debit  bal - Pos : Dr. = pos & Cr. = neg

	def balance_sheet(self, accounts=None, item=None, v=False): # TODO Needs to be optimized with:
		#self.gl['debit_acct_type'] = self.gl.apply(lambda x: self.get_acct_elem(x['debit_acct']), axis=1)
		all_accts = False
		if item is not None: # TODO Add support for multiple items maybe
			if v: print('BS Item: {}'.format(item))
			self.gl = self.gl[self.gl['item_id'] == item]
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			if v: print('BS GL: \n{}'.format(self.gl))
		if accounts is None: # Create a list of all the accounts
			all_accts = True
			# debit_accts = pd.unique(self.gl['debit_acct'])
			# credit_accts = pd.unique(self.gl['credit_acct'])
			# accounts = sorted(list(set(debit_accts) | set(credit_accts)))
			accounts = np.unique(self.gl[['debit_acct', 'credit_acct']].values).tolist()
		account_details = []

		# Create a list of tuples for all the accounts with their fundamental accounting element (asset,liab,eq,rev,exp)
		for acct in accounts:
			elem = self.get_acct_elem(acct)
			account_elem = (acct, elem)
			account_details.append(account_elem)

		# print('Account Details: \n{}'.format(account_details))

		# Group all the accounts together in lists based on their fundamental account element
		accounts = None
		assets = []
		liabilities = []
		equity = []
		revenues = []
		expenses = []
		for acct in account_details:
			if acct[1] == 'Asset':
				assets.append(acct[0])
			elif acct[1] == 'Liability':
				liabilities.append(acct[0])
			elif acct[1] == 'Equity':
				equity.append(acct[0])
			elif acct[1] == 'Revenue':
				revenues.append(acct[0])
			elif acct[1] == 'Expense':
				expenses.append(acct[0])
			else:
				continue

		# Create Balance Sheet dataframe to return
		self.bs = pd.DataFrame(columns=['line_item','balance']) # TODO Make line_item the index

		# TODO The below repeated sections can probably be handled more elegantly

		asset_bal = 0
		# if v: print('Asset Accounts: {}'.format(assets))
		for acct in assets:
			if v: print('Asset Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Asset Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Asset Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = debits - credits
			asset_bal += bal
			if v: print('Balance for {}: {}'.format(acct, bal))
			#if bal != 0: # TODO Not sure if should display empty accounts
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Assets:', 'balance':asset_bal}, ignore_index=True)

		liab_bal = 0
		for acct in liabilities:
			if v: print('Liability Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Liabilities Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Liabilities Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			liab_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Liabilities:', 'balance':liab_bal}, ignore_index=True)

		equity_bal = 0
		for acct in equity:
			if v: print('Equity Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Equity Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Equity Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			equity_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Equity:', 'balance':equity_bal}, ignore_index=True)

		rev_bal = 0
		for acct in revenues:
			if v: print('Revenue Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Revenues Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Revenues Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = credits - debits # Note reverse order of subtraction
			rev_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Revenues:', 'balance':rev_bal}, ignore_index=True)

		exp_bal = 0
		for acct in expenses:
			if v: print('Expense Account: {}'.format(acct))
			try:
				debits = self.gl.groupby('debit_acct').sum()['amount'][acct]
				if v: print('Debits: {}'.format(debits))
			except KeyError as e:
				if v: print('Expenses Debit Error: {} | {}'.format(e, repr(e)))
				debits = 0
			try:
				credits = self.gl.groupby('credit_acct').sum()['amount'][acct]
				if v: print('Credits: {}'.format(credits))
			except KeyError as e:
				if v: print('Expenses Credit Error: {} | {}'.format(e, repr(e)))
				credits = 0
			bal = debits - credits
			exp_bal += bal
			self.bs = self.bs.append({'line_item':acct, 'balance':bal}, ignore_index=True)
		self.bs = self.bs.append({'line_item':'Total Expenses:', 'balance':exp_bal}, ignore_index=True)

		retained_earnings = rev_bal - exp_bal
		self.bs = self.bs.append({'line_item':'Net Income:', 'balance':retained_earnings}, ignore_index=True)

		net_asset_value = asset_bal - liab_bal
		if net_asset_value == 0: # Two ways to calc NAV depending on accounts
			net_asset_value = equity_bal + retained_earnings

		total_equity = net_asset_value + liab_bal
		self.bs = self.bs.append({'line_item':'Equity+NI+Liab.:', 'balance':total_equity}, ignore_index=True)

		check = asset_bal - total_equity
		self.bs = self.bs.append({'line_item':'Balance Check:', 'balance':check}, ignore_index=True)

		self.bs = self.bs.append({'line_item':'Net Asset Value:', 'balance':net_asset_value}, ignore_index=True)

		if all_accts:
			if self.entity is None:
				self.bs.to_sql('balance_sheet', self.conn, if_exists='replace')
			else:
				entities = '_'.join(str(e) for e in self.entity)
				self.bs.to_sql('balance_sheet_' + entities, self.conn, if_exists='replace')
		if item is not None:
			self.refresh_ledger()
		return net_asset_value

	def print_bs(self):
		self.balance_sheet() # Refresh Balance Sheet
		with pd.option_context('display.max_rows', None, 'display.max_columns', None):
			print(self.bs)
		print('-' * DISPLAY_WIDTH)
		return self.bs

	def get_qty_txns(self, item=None, acct=None):
		rvsl_txns = self.gl[self.gl['description'].str.contains('RVSL')]['event_id'] # Get list of reversals
		# Get list of txns
		qty_txns = self.gl[(self.gl['item_id'] == item) & ((self.gl['debit_acct'] == acct) | (self.gl['credit_acct'] == acct)) & pd.notnull(self.gl['qty']) & (~self.gl['event_id'].isin(rvsl_txns))]
		#print('QTY TXNs:')
		#print(qty_txns)
		return qty_txns

	def get_qty(self, items=None, accounts=None, show_zeros=False, by_entity=False, credit=False, v=False):
		# if items == 'Weaving':
		# 	if v: print('Get Qty GL: \n{}'.format(self.gl))
		if not credit:
			acct_side = 'debit_acct'
		else:
			acct_side = 'credit_acct'
		all_accts = False
		single_item = False
		no_item = False
		if v: print('Items Given: {}'.format(items))
		if (items is None) or (items == '') or (not items):
			items = None
			no_item = True
		if isinstance(items, str):
			items = [x.strip() for x in items.split(',')]
			items = list(filter(None, items))
			if v: print('Select Items: {}'.format(items))
		if items is not None and len(items) == 1:
			single_item = True
			if v: print('Single Item: {}'.format(single_item))
		if (accounts is None) or (accounts == ''):
			if v: print('No account given.')
			all_accts = True
			if no_item:
				accounts = pd.unique(self.gl[acct_side])
				if v: print('Accounts Before Filter: \n{}'.format(accounts))
				# Filter for only Asset and Liability accounts
				accounts = [acct for acct in accounts if self.get_acct_elem(acct) == 'Asset' or self.get_acct_elem(acct) == 'Liability']
			else:
				item_txns = self.gl.loc[self.gl['item_id'].isin(items)]
				accounts = pd.unique(item_txns[acct_side])
			#credit_accts = pd.unique(self.gl['credit_acct']) # Not needed
			#accounts = list( set(accounts) | set(credit_accts) ) # Not needed
		if v: print('Accounts: {}\n'.format(accounts))
		if isinstance(accounts, str):
			accounts = [x.strip() for x in accounts.split(',')]
		accounts = list(filter(None, accounts))
		if by_entity:
			inventory = pd.DataFrame(columns=['entity_id','item_id','qty'])
		else:
			inventory = pd.DataFrame(columns=['item_id','qty'])
		if single_item:
			total_qty = 0
		for acct in accounts:
			#if v: print('GL: \n{}'.format(self.gl))
			if v: print('Acct: {}'.format(acct))
			if no_item: # Get qty for all items
				if v: print('No item given.')

				items = pd.unique(self.gl[self.gl[acct_side] == acct]['item_id'].dropna()).tolist() # Assuming you can't have a negative inventory
				#credit_items = pd.unique(self.gl[self.gl['credit_acct'] == acct]['item_id'].dropna()).tolist() # Causes issues
				#items = list( set(items) | set(credit_items) ) # Causes issues
				items = list(filter(None, items))
				if v: print('All Items: {}'.format(items))
			for item in items:
				if v: print('Item: {}'.format(item))
				if by_entity:
					entities = pd.unique(self.gl[self.gl['item_id'] == item]['entity_id'])
					if v: print('Entities: {}'.format(entities))
					for entity_id in entities:
						if v: print('Entity ID: {}'.format(entity_id))
						self.set_entity(entity_id)
						qty_txns = self.get_qty_txns(item, acct)
						if v: print('QTY TXNs by entity: \n{}'.format(qty_txns))
						try:
							debits = qty_txns.groupby(['debit_acct']).sum()['qty'][acct]
							if v: print('Debits: \n{}'.format(debits))
						except KeyError as e:
							if v: print('Error Debits: {} | {}'.format(e, repr(e)))
							debits = 0
						try:
							credits = qty_txns.groupby(['credit_acct']).sum()['qty'][acct]
							if v: print('Credits: \n{}'.format(credits))
						except KeyError as e:
							if v: print('Error Credits: {} | {}'.format(e, repr(e)))
							credits = 0
						qty = round(debits - credits, 0)
						if v: print('QTY: {}\n'.format(qty))
						inventory = inventory.append({'entity_id':entity_id, 'item_id':item, 'qty':qty}, ignore_index=True)
						#if v: print(inventory)
						self.reset()
					inventory['entity_id'] = pd.to_numeric(inventory['entity_id'])
				else:
					qty_txns = self.get_qty_txns(item, acct)
					if v: print('QTY TXNs: \n{}'.format(qty_txns))
					try:
						debits = qty_txns.groupby(['debit_acct']).sum()['qty'][acct]
						if v: print('Debits: {}'.format(debits))
					except KeyError as e:
						if v: print('Error Debits: {} | {}'.format(e, repr(e)))
						debits = 0
					try:
						credits = qty_txns.groupby(['credit_acct']).sum()['qty'][acct]
						if v: print('Credits: {}'.format(credits))
					except KeyError as e:
						if v: print('Error Credits: {} | {}'.format(e, repr(e)))
						credits = 0
					qty = round(debits - credits, 0)
					if v: print('QTY: {}\n'.format(qty))
					if single_item:
						total_qty += int(qty)
					else:
						inventory = inventory.append({'item_id':item, 'qty':qty}, ignore_index=True)
						#if v: print(inventory)
		if single_item and not by_entity:
			if v: print('Return Total Qty: ', total_qty)
			return total_qty
		if not show_zeros:
			inventory = inventory[(inventory.qty != 0)] # Ignores items completely sold
		if all_accts:
			if self.entity is None:
				inventory.to_sql('inventory', self.conn, if_exists='replace')
			else:
				entities = '_'.join(str(e) for e in self.entity)
				inventory.to_sql('inventory_' + entities, self.conn, if_exists='replace')
		return inventory

	# Used when booking journal entries to match related transactions
	def get_event(self):
		event_query = 'SELECT event_id FROM ' + self.ledger_name +' ORDER BY event_id DESC LIMIT 1;'
		cur = self.conn.cursor()
		cur.execute(event_query)
		event_id = cur.fetchone()
		cur.close()
		if event_id is None:
			event_id = 1
			return event_id
		else:
			return event_id[0] + 1

	def get_entity(self):
		if self.entity is None:
			entity = [1]
		else:
			entity = self.entity # TODO Long term solution
		return entity

	def journal_entry(self, journal_data=None):
		'''
			The heart of the whole system; this is how transactions are entered.
			journal_data is a list of transactions. Each transaction is a list
			of datapoints. This means an event with a single transaction
			would be encapsulated in as a single list within a list.
		'''
		if journal_data:
			if isinstance(journal_data, pd.DataFrame):
				journal_data = journal_data.values.tolist()
			elif isinstance(journal_data, pd.Series):
				journal_data = [journal_data.tolist()]
			elif not isinstance(journal_data[0], (list, tuple)):
				journal_data = [journal_data]
		cur = self.conn.cursor()
		if journal_data is None: # Manually enter a journal entry
			event = input('Enter an optional event_id: ')
			entity = input('Enter the entity_id: ')
			cp = input('Enter the counterparty id (or blank for itself): ')
			while True:
				try:
					date_raw = input('Enter a date as format yyyy-mm-dd: ')
					date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
					if date == 'NaT':
						date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
						date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
					datetime.datetime.strptime(date, '%Y-%m-%d')
					break
				except ValueError:
					print('Incorrect data format, should be YYYY-MM-DD.')
					continue
			loc = input('Enter an optional location: ')
			desc = input('Enter a description: ') + ' [M]'
			item = input('Enter an optional item_id: ')
			price = input('Enter an optional price: ')
			qty = input('Enter an optional quantity: ')
			debit = input('Enter the account to debit: ')
			if debit not in self.coa.index:
				print('\n' + debit + ' is not a valid account. Type "accts" command to view valid accounts.')
				return # TODO Make accounts foreign key constraint
			credit = input('Enter the account to credit: ')
			if credit not in self.coa.index:
				print('\n' + credit + ' is not a valid account. Type "accts" command to view valid accounts.')
				return
			while True:
				amount = input('Enter the amount: ')
				try: # TODO Maybe change to regular expression to prevent negatives
					x = float(amount)
					break
				except ValueError:
					print('Enter a number.')
					continue
			
			if event == '':
				event = str(self.get_event())
			if entity == '':
				entity = self.get_entity()
				if isinstance(entity, (list, tuple)):
					if len(entity) == 1:
						entity = entity[0]
					else:
						entity_str = [str(e) for e in entity]
						while True:
							entity_choice = input('There are multiple entities in this view. Choose from the following {}: '.format(entity))
							if entity_choice in entity_str:
								break
						entity = entity_choice
				else:
					entity = str(entity)
			if cp == '':
				cp = entity

			if qty == '': # TODO No qty and price default needed now
				qty = np.nan
			if price == '':
				price = np.nan

			values = (event, entity, cp, date, loc, desc, item, price, qty, debit, credit, amount)
			print(values)
			cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)', values)

		else: # Create journal entries by passing data to the function
			for je in journal_data:
				event = str(je[0])
				entity = je[1]
				if isinstance(entity, (list, tuple)):
					entity = entity[0]
				entity = str(entity)
				cp = je[2]
				if isinstance(cp, (list, tuple)):
					cp = cp[0]
				cp = str(cp)
				date = str(je[3])
				loc = str(je[4])
				desc = str(je[5])
				item  = str(je[6])
				price = str(je[7])
				qty = str(je[8])
				debit = str(je[9])
				credit = str(je[10])
				amount = str(je[11])

				if event == '' or event == 'nan':
					event = str(self.get_event())
				if entity == '' or entity == 'nan':
					entity = self.get_entity()
					if isinstance(entity, (list, tuple)):
						entity = entity[0]
					entity = str(entity)
				if cp == '' or cp == 'nan':
					cp = entity
				if date == 'NaT':
					date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
					date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
				try:
					datetime.datetime.strptime(date, '%Y-%m-%d')
				except ValueError:
					raise ValueError('Incorrect data format, should be YYYY-MM-DD.')

				if qty == '': # TODO No qty and price default needed now
					qty = np.nan
				if price == '':
					price = np.nan

				values = (event, entity, cp, date, loc, desc, item, price, qty, debit, credit, amount)
				print(values)
				cur.execute('INSERT INTO ' + self.ledger_name + ' VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)', values)

		self.conn.commit()
		txn_id = cur.lastrowid
		cur.close()
		self.refresh_ledger() # Ensures the gl is in sync with the db
		self.balance_sheet() # Ensures the bs is in sync with the ledger
		self.get_qty() # Ensures the inv is in sync with the ledger
		#return values # TODO Add all entries to list before returning

	def sanitize_ledger(self): # This is not implemented yet
		dupes = self.gl[self.gl.duplicated(['entity_id','date','description','item_id','price','qty','debit_acct','credit_acct','amount'])]
		dupes_to_drop = dupes.index.tolist()
		dupes_to_drop = ', '.join(str(x) for x in dupes_to_drop)
		# Delete dupes from db
		if not dupes.empty:
			cur = self.conn.cursor()
			cur.execute('DELETE FROM ' + self.ledger_name + ' WHERE txn_id IN (' + dupes_to_drop + ')')
			self.conn.commit()
			cur.close()
		self.refresh_ledger()

	def load_gl(self, infile=None, flag=None):
		if infile is None:
			infile = input('Enter a filename: ')
			#infile = 'data/rbc_sample_2019-01-27.csv' # For testing
			#infile = 'data/legacy_ledger_2019-01-25.csv' # For testing
		if flag is None:
			flag = input('Enter a flag (rbc, legacy, or none): ')
			#flag = 'rbc' # For testing
			#flag = 'legacy' # For testing
		try:
			with open(infile, 'r') as f:
				if flag == 'legacy':
					load_gl = pd.read_csv(f, header=1, keep_default_na=False)
				else:
					load_gl = pd.read_csv(f, keep_default_na=False)
		except Exception as e:
			print('Error: {} | {}'.format(e, repr(e)))
			load_gl = pd.DataFrame()
		print(load_gl)
		print('-' * DISPLAY_WIDTH)
		if flag == 'rbc':
			load_gl['dupe'] = load_gl.duplicated(keep=False)
			for index, row in load_gl.iterrows():
				if row['dupe']:
					unique_desc = row['Description 2'] + ' - ' + str(index)
					load_gl.at[index, 'Description 2'] = unique_desc
			load_gl.drop('dupe', axis=1, inplace=True)
			rbc_txn = pd.DataFrame()
			rbc_txn['event_id'] = ''
			rbc_txn['entity_id'] = ''
			rbc_txn['cp_id'] = ''
			rbc_txn['date'] = load_gl['Transaction Date']
			rbc_txn['loc'] = ''
			rbc_txn['desc'] = load_gl['Description 1'] + ' | ' + load_gl['Description 2']
			rbc_txn['item_id'] = ''
			rbc_txn['price'] = ''
			rbc_txn['qty'] = ''
			rbc_txn['debit_acct'] = np.where(load_gl['CAD$'] > 0, load_gl['Account Type'], 'Uncategorized')
			rbc_txn['credit_acct'] = np.where(load_gl['CAD$'] < 0, load_gl['Account Type'], 'Uncategorized')
			rbc_txn['amount'] = abs(load_gl['CAD$'])
			lol = rbc_txn.values.tolist()
			self.journal_entry(lol)
			self.sanitize_ledger()
		elif flag == 'legacy':
			load_gl = load_gl[:-3]
			load_gl['Category 3'] = load_gl['Category 3'].replace(r'^\s*$', np.nan, regex=True)
			load_gl['Category 3'].fillna('Uncategorized', inplace=True)
			load_gl['dupe'] = load_gl.duplicated(keep=False)
			for index, row in load_gl.iterrows():
				if row['dupe']:
					unique_desc = row['Description 2'] + ' - ' + str(index)
					load_gl.at[index, 'Description 2'] = unique_desc
			load_gl.drop('dupe', axis=1, inplace=True)
			load_gl['Amount'] = [float(x.replace('$','').replace(',','').replace(')','').replace('(','-')) if x else 0 for x in load_gl['Amount']]
			leg_txn = pd.DataFrame()
			leg_txn['event_id'] = ''
			leg_txn['entity_id'] = ''
			leg_txn['cp_id'] = ''
			leg_txn['date'] = load_gl['Transaction Date']
			leg_txn['loc'] = ''
			leg_txn['desc'] = load_gl['Description 1'] + ' | ' + load_gl['Description 2']
			leg_txn['item_id'] = ''
			leg_txn['price'] = ''
			leg_txn['qty'] = ''
			leg_txn['debit_acct'] = np.where(load_gl['Amount'] > 0, load_gl['Account Type'], load_gl['Category 3'])
			leg_txn['credit_acct'] = np.where(load_gl['Amount'] < 0, load_gl['Account Type'], load_gl['Category 3'])
			leg_txn['amount'] = abs(load_gl['Amount'])
			lol = leg_txn.values.tolist()
			self.journal_entry(lol)
			self.sanitize_ledger()
		else:
			if 'txn_id' in load_gl.columns.values:
				load_gl.set_index('txn_id', inplace=True)
			lol = load_gl.values.tolist()
			self.journal_entry(lol)	

	def export_gl(self):
		self.reset()
		outfile = self.ledger_name + '_' + datetime.datetime.today().strftime('%Y-%m-%d_%H-%M-%S') + '.csv'
		save_location = 'data/'
		try:
			self.gl.to_csv(save_location + outfile, date_format='%Y-%m-%d')
			print('File saved as ' + save_location + outfile)
		except Exception as e:
			print('Error: {}'.format(e))

	def remove_entries(self, txns=None):
		if txns is None:
			txns = []
			txns = txns.append(input('Which transaction ID would you like to remove? '))
		cur = self.conn.cursor()
		for txn in txns:
			cur.execute('DELETE FROM '+ self.ledger_name +' WHERE txn_id=?', (txn,))
		self.conn.commit()
		cur.close()
		print('Removed {} entries.'.format(len(txns)))
		self.refresh_ledger()

	def reversal_entry(self, txn=None, date=None): # This func effectively deletes a transaction
		if txn is None:
			txn = input('Which txn_id to reverse? ')
		rvsl_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = '+ txn + ';' # TODO Use gl dataframe
		cur = self.conn.cursor()
		cur.execute(rvsl_query)
		rvsl = cur.fetchone()
		logging.debug('rvsl: {}'.format(rvsl))
		cur.close()
		if '[RVSL]' in rvsl[4]:
			print('Cannot reverse a reversal. Enter a new entry instead.')
			return
		if date is None: # rvsl[7] or np.nan
			date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
			date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
		rvsl_entry = [[ rvsl[1], rvsl[2], rvsl[3], date, rvsl[5], '[RVSL]' + rvsl[6], rvsl[7], rvsl[8] or '', rvsl[9] or '', rvsl[11], rvsl[10], rvsl[12] ]]
		self.journal_entry(rvsl_entry)

	def split(self, txn=None, debit_acct=None, credit_acct=None, amount=None, date=None):
		if txn is None:
			txn = input('Which txn_id to split? ')
		self.reversal_entry(txn)
		split_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = '+ txn + ';' # TODO Use gl dataframe
		cur = self.conn.cursor()
		cur.execute(split_query)
		split = cur.fetchone()
		cur.close()
		if amount is None:
			split_amt = float(input('How much to split by? '))
			while split_amt > split[12]:
				split_amt = float(input('That is too much. How much to split by? '))
		if debit_acct is None:
			debit_acct = input('Which debit account to split with? ')
			if debit_acct == '':
				debit_acct = split[10]
		if credit_acct is None:
			credit_acct = input('Which credit account to split with? ')
			if credit_acct == '':
				credit_acct = split[11]
		if date is None:
			date_raw = datetime.datetime.today().strftime('%Y-%m-%d')
			date = str(pd.to_datetime(date_raw, format='%Y-%m-%d').date())
		orig_split_entry = [ split[1], split[2], split[3], date, split[5], split[6], split[7], split[8] or '', split[9] or '', split[10], split[11], split[12] - split_amt ]
		new_split_entry = [ split[1], split[2], split[3], date, split[5], split[6], split[7], split[8] or '', split[9] or '', debit_acct, credit_acct, split_amt ]
		split_event = [orig_split_entry, new_split_entry]
		self.journal_entry(split_event)

	def uncategorize(self, txn=None, debit_acct=None, credit_acct=None):
		if txn is None:
			txn = input('Enter the transaction number: ')
		uncat_query = 'SELECT * FROM '+ self.ledger_name +' WHERE txn_id = '+ txn + ';' # TODO Use gl dataframe
		cur = self.conn.cursor()
		cur.execute(uncat_query)
		entry = cur.fetchone()
		#print('Entry: \n{}'.format(entry))
		debit_acct = entry[10]
		if entry[10] == 'Uncategorized':
			if debit_acct is None:
				debit_acct = input('Enter the account to debit: ')
			if debit_acct not in self.coa.index:
				print('\n' + debit + ' is not a valid account.')
		credit_acct = entry[11]
		if entry[11] == 'Uncategorized':
			if credit_acct is None:
				credit_acct = input('Enter the account to credit: ')
			if credit_acct not in self.coa.index:
				print('\n' + credit + ' is not a valid account.')
		new_entry = [ entry[1], entry[2], entry[3], entry[4], entry[5], entry[6], entry[7], entry[8] or '', entry[9] or '', debit_acct, credit_acct, entry[12] ]
		#print('New Entry: \n{}'.format(new_entry))
		new_cat_query = 'UPDATE '+ self.ledger_name +' SET debit_acct = \'' + debit_acct + '\', credit_acct = \'' + credit_acct + '\' WHERE txn_id = '+ txn + ';'
		#print('New Cat Query: \n{}'.format(new_cat_query))
		cur.execute(new_cat_query)
		cur.close()
		self.refresh_ledger()
		return new_entry

	def hist_cost(self, qty=None, item=None, acct=None, remaining_txn=False, avg_cost=False, v=False):
		v2 = False
		if qty is None:
			qty = int(input('Enter quantity: '))
		if item is None:
			item = input('Enter item: ')
		if acct is None:
			acct = 'Inventory' #input('Enter account: ') # TODO Remove this maybe
		if qty == 0:
			return 0

		if avg_cost: # TODO Test Avg Cost
			if v: print('Getting average historical cost of {} for {} qty.'.format(item, qty))
			total_balance = ledger.balance_sheet([acct], item=item)
			if v: print('Total Balance: {}'.format(total_balance))
			total_qty = ledger.get_qty(items=item, accounts=[acct])
			if v: print('Total Qty: {}'.format(total_qty))
			amount = qty * (total_balance / total_qty)
			if v: print('Avg. Cost Amount: {}'.format(amount))
			return amount
		else:
			if v: print('Getting historical cost of {} for {} qty.'.format(item, qty))
			qty_txns = self.get_qty_txns(item, acct)
			m1 = qty_txns.credit_acct == acct
			m2 = qty_txns.credit_acct != acct
			credit_qtys = -qty_txns['qty']
			debit_qtys = qty_txns['qty']
			qty_txns = np.select([m1, m2], [credit_qtys, debit_qtys])
			if v: print('Qty TXNs: {} \n{}'.format(len(qty_txns), qty_txns))

			# Find the first lot of unsold items
			count = 0
			qty_back = self.get_qty(item, [acct]) # TODO Confirm this work when there are multiple different lots of buys and sells in the past
			if v: print('Qty to go back: {}'.format(qty_back))
			qty_change = []
			qty_change.append(qty_back)
			# neg = False
			for txn in qty_txns[::-1]:
				if v2: print('Hist TXN Item: {}'.format(txn))
				# if txn < 0:
				# 	neg = True
				count -= 1
				if v2: print('Hist Count: {}'.format(count))
				qty_back -= txn
				qty_change.append(qty_back)
				if v2: print('Qty Back: {}'.format(qty_back))
				if v: print('Count: {} | TXN: {} | Qty Back: {}'.format(count, txn, qty_back))
				if qty_back == 0:
					break
				# elif qty_back > 0 and neg:
				# 	count += 1
				# 	if v: print('Hist Count Neg: {}'.format(count))
				# 	neg = False

			if v2: print('Qty Back End: {}'.format(qty_back))
			start_qty = qty_txns[count]
			if v: print('Start Qty lot: {}'.format(start_qty))

			qty_txns_gl = self.get_qty_txns(item, acct)
			qty_txns_gl_check = qty_txns_gl.loc[qty_txns_gl['credit_acct'] == acct]
			if not qty_txns_gl_check.empty:
				mask = qty_txns_gl.credit_acct == acct
				#print('Mask: \n{}'.format(mask))
				#qty_txns_gl_flip = qty_txns_gl.loc[mask, 'qty'] # Testing
				#print('qty_txns_gl_flip: \n{}'.format(qty_txns_gl_flip))
				# flip_qty = qty_txns_gl['qty'] * -1
				warnings.filterwarnings('ignore')
				# WithCopyWarning: Warning here
				# qty_txns_gl.loc[mask, 'qty'] = flip_qty
				#qty_txns_gl.loc[mask, 'qty'] = qty_txns_gl['qty'] * -1 # Old
				qty_txns_gl.loc[mask, 'qty'] *= -1

			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				if v: print('QTY TXNs GL: {} \n{}'.format(len(qty_txns_gl), qty_txns_gl))
			if v: print('Hist Count Final: {}'.format(count))
			start_index = qty_txns_gl.index[count]
			if v2: print('Start Index: {} | Len: {}'.format(start_index, len(qty_txns_gl)))
			if remaining_txn:
				avail_txns = qty_txns_gl.loc[start_index:]
				return avail_txns
			if v2: print('Qty Change List: \n{}'.format(qty_change))
			if len(qty_change) >= 3:
				avail_qty = start_qty - qty_change[-1]#-3]# Portion of first lot of unsold items that has not been sold
			else:
				avail_qty = start_qty

			if v: print('Available qty in start lot: {}'.format(avail_qty))
			amount = 0
			if qty <= avail_qty: # Case when first available lot covers the need
				if v2: print('Hist Qty: {}'.format(qty))
				price_chart = pd.DataFrame({'price':[self.gl.loc[start_index]['price']],'qty':[qty]})
				if price_chart.shape[0] >= 2:
					print('Historical Cost Price Chart: \n{}'.format(price_chart))
				amount = price_chart.price.dot(price_chart.qty)
				print('Historical Cost Case | One for {} {}: {}'.format(qty, item, amount))
				return amount

			price_chart = pd.DataFrame({'price':[self.gl.loc[start_index]['price']],'qty':[max(avail_qty, 0)]}) # Create a list of lots with associated price
			qty = qty - avail_qty # Sell the remainder of first lot of unsold items
			if v2: print('Historical Cost Price Chart Start: \n{}'.format(price_chart))
			if v2: print('Qty Left to be Sold First: {}'.format(qty))
			count += 1
			if v: print('Count First: {}'.format(count))
			current_index = qty_txns_gl.index[count]
			if v2: print('Current Index First: {}'.format(current_index))
			while qty > 0: # Running amount of qty to be sold
				if v2: print('QTY Check: {}'.format(qty_txns_gl.loc[current_index]['qty']))
				# while qty_txns_gl.loc[current_index]['qty'] < 0: # TODO Confirm this is not needed
				# 	count += 1
				# 	if v: print('Count When Neg: {}'.format(count))
				# 	current_index = qty_txns_gl.index[count]
				current_index = qty_txns_gl.index[count]
				if v2: print('Current Index: {}'.format(current_index))
				if v: print('Qty Left to be Sold 1: {}'.format(qty))
				if v: print('Current TXN Qty: {} | {}'.format(qty_txns_gl.loc[current_index]['qty'], self.gl.loc[current_index]['qty']))
				if qty < self.gl.loc[current_index]['qty']: # Final case when the last sellable lot is larger than remaining qty to be sold
					price_chart = price_chart.append({'price':self.gl.loc[current_index]['price'], 'qty':max(qty, 0)}, ignore_index=True)
					if price_chart.shape[0] >= 2:
						print('Historical Cost Price Chart: \n{}'.format(price_chart))
					amount = price_chart.price.dot(price_chart.qty) # Take dot product
					print('Historical Cost Case | Two for {} {}: {}'.format(qty, item, amount))
					return amount
				
				price_chart = price_chart.append({'price':self.gl.loc[current_index]['price'], 'qty':max(self.gl.loc[current_index]['qty'], 0)}, ignore_index=True)
				qty = qty - self.gl.loc[current_index]['qty']
				if v: print('Qty Left to be Sold 2: {}'.format(qty))
				count += 1
				if v: print('Count: {}'.format(count))

			if price_chart.shape[0] >= 2:
				print('Historical Cost Price Chart: \n{}'.format(price_chart))
			amount = price_chart.price.dot(price_chart.qty) # If remaining lot perfectly covers remaining amount to be sold
			print('Historical Cost Case | Three for {} {}: {}'.format(qty, item, amount))
			return amount

	def bs_hist(self): # TODO Optimize this so it does not recalculate each time
		gl_entities = pd.unique(self.gl['entity_id'])
		logging.info(gl_entities)
		dates = pd.unique(self.gl['date'])
		logging.info(dates)

		cur = self.conn.cursor()
		create_bs_hist_query = '''
			CREATE TABLE IF NOT EXISTS hist_bs (
				date date NOT NULL,
				entity text NOT NULL,
				assets real NOT NULL,
				liabilities real NOT NULL,
				equity real NOT NULL,
				revenues real NOT NULL,
				expenses real NOT NULL,
				net_income real NOT NULL,
				equity_ni_liab real NOT NULL,
				bal_check real NOT NULL,
				net_asset_value real NOT NULL
			);
			'''
		cur.execute(create_bs_hist_query)
		cur.execute('DELETE FROM hist_bs')
		for entity in gl_entities:
			logging.info(entity)
			self.set_entity(entity)
			for date in dates:
				logging.info(entity)
				self.set_date(date)
				logging.info(date)
				self.balance_sheet()
				self.bs.set_index('line_item', inplace=True)
				col0 = str(entity)
				col1 = self.bs.loc['Total Assets:'][0]
				col2 = self.bs.loc['Total Liabilities:'][0]
				col3 = self.bs.loc['Total Equity:'][0]
				col4 = self.bs.loc['Total Revenues:'][0]
				col5 = self.bs.loc['Total Expenses:'][0]
				col6 = self.bs.loc['Net Income:'][0]
				col7 = self.bs.loc['Equity+NI+Liab.:'][0]
				col8 = self.bs.loc['Balance Check:'][0]
				col9 = self.bs.loc['Net Asset Value:'][0]
				
				data = (date,col0,col1,col2,col3,col4,col5,col6,col7,col8,col9)
				logging.info(data)
				cur.execute('INSERT INTO hist_bs VALUES (?,?,?,?,?,?,?,?,?,?,?)', data)
		self.conn.commit()
		cur.execute('PRAGMA database_list')
		db_path = cur.fetchall()[0][-1]
		db_name = db_path.rsplit('/', 1)[-1]
		cur.close()

		self.hist_bs = pd.read_sql_query('SELECT * FROM hist_bs;', self.conn, index_col=['date','entity'])
		return self.hist_bs, db_name

		# TODO Add function to book just the current days bs to hist_bs

	def print_hist(self):
		db_name = self.bs_hist()[1]
		path = 'data/bs_hist_' + db_name[:-3] + '.csv'
		self.hist_bs.to_csv(path, index=True)
		with pd.option_context('display.max_rows', None, 'display.max_columns', None): # To display all the rows
			print(self.hist_bs)
		print('File saved to: {}'.format(path))
		print('-' * DISPLAY_WIDTH)
		return self.hist_bs

	def fix_qty(self): # Temp qty fix function
		cur = self.conn.cursor()
		qty = np.nan
		#print('QTY: {}'.format(qty))
		value = (qty,)
		#print('Value: {}'.format(value))
		cur.execute('UPDATE ' + self.ledger_name + ' SET qty = (?) WHERE qty = 1', value)
		self.conn.commit()
		cur.close()
		print('QTYs converted.')


def main(conn=None, command=None, external=False):
	parser = argparse.ArgumentParser()
	parser.add_argument('-db', '--database', type=str, help='The name of the database file.')
	parser.add_argument('-l', '--ledger', type=str, help='The name of the ledger.')
	parser.add_argument('-e', '--entity', type=int, help='A number for the entity.')
	parser.add_argument('-c', '--command', type=str, help='A command for the program.')
	# Dummy args to allow it work with econ.py
	parser.add_argument('-sim', '--simulation', action='store_true', help='Run on historical data.')
	parser.add_argument('-d', '--delay', type=int, default=0, help='The amount of seconds to delay each econ update.')
	parser.add_argument('-P', '--players', type=int, default=1, help='The number of players in the econ sim.')
	parser.add_argument('-p', '--population', type=int, default=2, help='The number of people in the econ sim.')
	parser.add_argument('-r', '--reset', action='store_true', help='Reset the sim!')
	parser.add_argument('-rand', '--random', action='store_false', help='Remove randomness from the sim!')
	parser.add_argument('-s', '--seed', type=str, help='Set the seed for the randomness in the sim.')
	parser.add_argument('-i', '--items', type=str, help='The name of the items csv config file.')
	parser.add_argument('-t', '--time', type=int, help='The number of days the sim will run for.')
	parser.add_argument('-cap', '--capital', type=float, help='Amount of capital each player to start with.')
	parser.add_argument('-u', '--users', type=int, nargs='?', const=-1, help='Play the sim!')
	parser.add_argument('-U', '--Users', type=int, nargs='?', const=-1, help='Play the sim as an individual!')
	args = parser.parse_args()

	if args.database is not None:
		conn = args.database
	accts = Accounts(conn=conn)
	ledger = Ledger(accts, ledger_name=args.ledger, entity=args.entity)
	if command is None:
		command = args.command

	while True: # TODO Make this a function that has the command passed in as an argument
		if args.command is None and not external:
			command = input('\nType one of the following commands:\nBS, GL, JE, RVSL, loadGL, Accts, addAcct, loadAccts, help, exit\n')
		# TODO Add help command to list full list of commands
		if command.lower() == 'gl':
			ledger.print_gl()
			if args.command is not None: exit()
		elif command.lower() == 'exportgl':
			ledger.export_gl()
			if args.command is not None: exit()
		elif command.lower() == 'loadgl':
			ledger.load_gl()
			if args.command is not None: exit()
		elif command.lower() == 'accts':
			accts.print_accts()
			if args.command is not None: exit()
		elif command.lower() == 'addacct':
			accts.add_acct()
			if args.command is not None: exit()
		elif command.lower() == 'removeacct':
			accts.remove_acct()
			if args.command is not None: exit()
		elif command.lower() == 'loadaccts':
			accts.load_accts()
			if args.command is not None: exit()
		elif command.lower() == 'exportaccts':
			accts.export_accts()
			if args.command is not None: exit()
		elif command.lower() == 'dupes':
			accts.drop_dupe_accts()
			if args.command is not None: exit()
		elif command.lower() == 'je':
			ledger.journal_entry()
			if args.command is not None: exit()
		elif command.lower() == 'rvsl':
			ledger.reversal_entry()
		elif command.lower() == 'split':
			ledger.split()
		elif command.lower() == 'uncategorize':
			ledger.uncategorize()
			if args.command is not None: exit()
		elif command.lower() == 'bs':
			ledger.print_bs()
			if args.command is not None: exit()
		elif command.lower() == 'qty':
			item = input('Which item or ticker? ')#.lower()
			acct = input('Which account? ')#.title()
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(ledger.get_qty(item, acct))
			if args.command is not None: exit()
		elif command.lower() == 'inv':
			with pd.option_context('display.max_rows', None, 'display.max_columns', None):
				print(ledger.get_qty(by_entity=True, v=True))
			if args.command is not None: exit()
		elif command.lower() == 'entity':
			ledger.set_entity()
			if args.command is not None: exit()
		elif command.lower() == 'date':
			ledger.set_date()
			if args.command is not None: exit()
		elif command.lower() == 'startdate':
			ledger.set_start_date()
			if args.command is not None: exit()
		elif command.lower() == 'txn':
			ledger.set_txn()
			if args.command is not None: exit()
		elif command.lower() == 'starttxn':
			ledger.set_start_txn()
			if args.command is not None: exit()
		elif command.lower() == 'reset':
			ledger.reset()
			if args.command is not None: exit()
		elif command.lower() == 'hist':
			ledger.print_hist()
			if args.command is not None: exit()
		elif command.lower() == 'entities':
			accts.print_entities()
			if args.command is not None: exit()
		elif command.lower() == 'items':
			accts.print_items()
			if args.command is not None: exit()
		elif command.lower() == 'addentity':
			accts.add_entity()
			if args.command is not None: exit()
		elif command.lower() == 'additem':
			accts.add_item()
			if args.command is not None: exit()
		elif command.lower() == 'loadentities':
			accts.load_entities()
			if args.command is not None: exit()
		elif command.lower() == 'loaditems':
			accts.load_items()
		elif command.lower() == 'table':
			accts.print_table()
		elif command.lower() == 'exporttable':
			accts.export_table()

		elif command.lower() == 'db':
			if args.database is not None:
				db = args.database
			else:
				db = accts.db
			print('Current database: {}'.format(db))
		elif command.lower() == 'bal':
			acct = input('Which account? ').title()
			tbal_start = time.perf_counter()
			bal = ledger.balance(acct, v=False)
			tbal_end = time.perf_counter()
			print(bal)
			print('Bal took {:,.2f} sec.'.format((tbal_end - tbal_start)))

			tbal_start = time.perf_counter()
			bal = ledger.print_bs()
			tbal_end = time.perf_counter()
			print(bal)
			print('BS took {:,.2f} sec.'.format((tbal_end - tbal_start)))

		elif command.lower() == 'histcost':
			result = ledger.hist_cost(400, 'Rock', 'Inventory', avg_cost=True, v=True)
			print('Historical cost of {} {}: {}'.format(400, 'Rock', result))
			if args.command is not None: exit()
		elif command.lower() == 'width': # TODO Try and make this work
			DISPLAY_WIDTH = int(input('Enter number for display width: '))
			if args.command is not None: exit()

		elif command.lower() == 'help' or command.lower() == 'accthelp':
			commands = {
				'accts': 'View the Chart of Accounts with their types.',
				'gl': 'View the General Ledger.',
				'bs': 'View the Balance Sheet and Income Statement.',
				'entity': 'View only data related to the entity set.',
				'date': 'Set the date to view the Balance Sheet up to.',
				'startdate': 'Set the start date to view the Income Statement from.',
				'reset': 'Resets both the entity and dates, to view for all entities and for all dates.',
				'je': 'Book a journal entry to the General Ledger.',
				'addacct': 'Add an account to the Chart of Accounts.',
				'rvsl': 'Reverse a journal entry on the General Ledger.',
				'removeacct': 'Remove an account on the Chart of Accounts.',
				'qty': 'Get the quantity of a particular item or all items if none is specified.',
				'more': 'List more commands... (WIP)',
				'exit': 'Exit out of the program.'
			}
			cmd_table = pd.DataFrame(commands.items(), columns=['Command', 'Description'])
			with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
				print(cmd_table)
		elif command.lower() == 'more' or command.lower() == 'acctmore':
			commands = {
				'split': 'Split a journal entry into more granular entries.',
				'uncategorize': 'For journal entries that are uncategorized, assign them to a new account.',
				'txn': 'Set the date to view the Balance Sheet up to.',
				'starttxn': 'Set the start date to view the Income Statement from.',
				'exportgl': 'Export the General Ledger to csv.',
				'importgl': 'Import the General Ledger from csv.',#'Also supports loading trasnactions from RBC online banking and a legacy account system.',
				'exportaccts': 'Export the Chart of Accounts to csv.',
				'importaccts': 'Import the Chart of Accounts from csv.',
				'table': 'Display any table in the database given its name.',
				'exit': 'Exit out of the program.'
			}
			cmd_table = pd.DataFrame(commands.items(), columns=['Command', 'Description'])
			with pd.option_context('display.max_colwidth', 200, 'display.colheader_justify', 'left'):
				print(cmd_table)
		elif command.lower() == 'exit' or args.command is not None:
			exit()
		else:
			# print('Not a valid command. Type "exit" to close or "help" for more info.')
			print('"{}" is not a valid command. Type "exit" to close or "help" for more options.'.format(command))
		if external:
			break

if __name__ == '__main__':
	main()