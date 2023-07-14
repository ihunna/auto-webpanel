from app_configs import httpx,SearchEngine,time,random,ThreadPoolExecutor,as_completed,json,datetime
from scheduler import Scheduler


class TASKS:
	def __init__(self) -> None:
		pass
	
	def get_location(self,zipcode):
		try:
			states = {
				"AL": "Alabama",
				"AK": "Alaska",
				"AZ": "Arizona",
				"AR": "Arkansas",
				"CA": "California",
				"CO": "Colorado",
				"CT": "Connecticut",
				"DE": "Delaware",
				"FL": "Florida",
				"GA": "Georgia",
				"HI": "Hawaii",
				"ID": "Idaho",
				"IL": "Illinois",
				"IN": "Indiana",
				"IA": "Iowa",
				"KS": "Kansas",
				"KY": "Kentucky",
				"LA": "Louisiana",
				"ME": "Maine",
				"MD": "Maryland",
				"MA": "Massachusetts",
				"MI": "Michigan",
				"MN": "Minnesota",
				"MS": "Mississippi",
				"MO": "Missouri",
				"MT": "Montana",
				"NE": "Nebraska",
				"NV": "Nevada",
				"NH": "New Hampshire",
				"NJ": "New Jersey",
				"NM": "New Mexico",
				"NY": "New York",
				"NC": "North Carolina",
				"ND": "North Dakota",
				"OH": "Ohio",
				"OK": "Oklahoma",
				"OR": "Oregon",
				"PA": "Pennsylvania",
				"RI": "Rhode Island",
				"SC": "South Carolina",
				"SD": "South Dakota",
				"TN": "Tennessee",
				"TX": "Texas",
				"UT": "Utah",
				"VT": "Vermont",
				"VA": "Virginia",
				"WA": "Washington",
				"WV": "West Virginia",
				"WI": "Wisconsin",
				"WY": "Wyoming"
			}

			search = SearchEngine()
			location = search.by_zipcode(zipcode=zipcode)
			city = location.major_city
			state = states.get(location.state)
			area_code = str(location.area_code_list).split(',')
			area_code = random.choice(area_code)

			locaion = {
				'city':city,
				'state':state,
				'area_code':area_code
			}
			return True,locaion
		except Exception as error:
			return False, error

	def create_scheduler(self,scheduler,host,swipe_configs,payload:dict={}):
		try:
			session_count = swipe_configs['swipe_session_count']
			swipe_duration = swipe_configs['swipe_duration']
			start_date = swipe_configs['op_start_at']
			end_date = swipe_configs['op_end_at']

			start_date = scheduler.get_date_format(start_date)
			end_date = scheduler.get_date_format(end_date)
			start_date,end_date = datetime(*start_date), datetime(*end_date)
			cron_exp = scheduler.generate_cron_expression(start_date,
							end_date,session_count=session_count,
							operation_duration=swipe_duration,
							daily_percent=swipe_configs['daily_percent'])
			
			schedule = scheduler.create(cron_exp,host,payload=payload)
			if not schedule[0]:return False,schedule[1]
			return True, schedule[1]
		except Exception as error:
			return False,error

	def create_accounts(self,
			account:int =None,
			server_option:str = None,
			nb_of_images:int=5,
			nb_of_accounts:int = 1,
			names:list=None,
			handles:list=None,
			bios:list = None,
			task_id:str = None,
			profile_images:list = None,
			verification_images:dict = None,
			age_range:str = '18-60',
			gender:str= None,
			gender_data:dict = None,
			cities:list = None,
			proxies:list = None,
			user_agents:list = None,
			accounts:list = None,
			url:str = None,
			token:str = None):
		URL = f'{url}/account'
		try:
			with httpx.Client(timeout=httpx.Timeout(200.0)) as session:
				session.headers = {
					'Content-Type':'application/json',
					'Authorization': f'Bearer {token}'
				}

				json_data = {
					'server_option':server_option,
					'nb_of_accounts':nb_of_accounts,
					'names':names,
					'bios':bios,
					'handles':handles,
					'profile_images':profile_images,
					"nb_of_images":nb_of_images,
					'verification_images':verification_images,
					'age-range':age_range,
					'gender':gender,
					'gender_data':gender_data,
					'cities':cities,
					'proxies':proxies,
					'user_agents':user_agents,
					'accounts':accounts,
				}

				flow = session.put(URL,json=json_data)
				if flow.status_code > 299:return False,flow.text
				
				print(f'\nWaiting for account to be created for: {account}')
				status = 'PENDING_CREATION'
				account_id = flow.json()['accounts'][0].get('id')
				while status == 'PENDING_CREATION':
					flow = session.get(f"{URL}/{account_id}")
					if flow.status_code  > 299:return False,flow.text
					status = flow.json()['status']
					time.sleep(60)
				account_details = flow.json()
				print(f'\nAccount created for: {account + 1}')
				return True,account_details

		except Exception as error:
			return False,error

	def start_account_creation(self,
			accounts_ref=None,
			tasks_ref=None,
			files_ref=None,
			used_emails:list=None,
			swipe_configs:dict=None,
			worker:str = None,
			SERVER:str = None,
			server_option:str ='webapi',
			nb_of_images:int=None,
			op_count:int = 1,
			names:list=None,
			bios:list = None,
			handles:list=None,
			max_workers:int = 10,
			task_id:str = None,
			images:list = None,
			verification_images:dict = None,
			age_range:str = None,
			gender:str = None,
			gender_data:dict= None,
			cities:list = None,
			proxies:list = None,
			user_agents:list = None,
			accounts:list = None,
			token:str = None,
			url:str=None):
	
		print('\nACCOUNT CREATION STARTED \n')
		success,msg,task_status = False,'',''
		fails,passes,completed= 0,0,0
		created_accounts = []

		try:
			kwargs=[{
				'account':f'account {i + 1}',
				'server_option':server_option,
				'nb_of_accounts':1,
				'names':names[i],
				'accounts':accounts[i],
				'bios':bios[i],
				'handles':handles[i],
				'cities':cities[i],
				'proxies':proxies[i],
				'user_agents':user_agents[i],
				'age_range':age_range,
				'gender':gender,
				'gender_data':gender_data,
				'profile_images':images,
				'nb_of_images':nb_of_images,
				'verification_images':verification_images,
				'url':url,
				'token':token
			}for i in range(op_count)]

			with ThreadPoolExecutor(max_workers=max_workers) as executor:
				futures = []
				for kwargs in kwargs:
					future = executor.submit(self.create_accounts, **kwargs)
					futures.append(future)

				for future in as_completed(futures):
					result = future.result()
					if result[0]:
						account = result[1]
						completed += 1
						print(account)
						if account.get('status') == 'CREATION_ERROR':
							fails += 1
							msg = f'{fails} account of {op_count} failed and {op_count - (fails+passes)} waiting to be created'
							tasks_ref.document(task_id).update({
								'message':msg,
								'progress':(completed / op_count) * 100,
								'successful':passes,
								'failed':fails
								})
							continue
						account['last_updated'] = str(datetime.now())
						accounts_ref.document(account['id']).set(account)
						created_accounts.append(account['id'])
						
						passes += 1
						msg = f'{passes} account of {op_count} created successfully and {op_count - (passes+fails)} waiting to be created'
						tasks_ref.document(task_id).update({
							'message':msg,
							'progress':(completed / op_count) * 100,
							'successful':passes,
							'failed':fails
							})
						
						used_emails.append(f"{account['email']}:{account['password']}")
						files_ref.document('Used Emails').update({'content':used_emails})
						
					else:
						fails += 1
						msg = f'{fails} account of {op_count} failed and {op_count - (fails+passes)} waiting to be created'
						tasks_ref.document(task_id).update({
							'message':msg,
							'progress':(completed / op_count) * 100,
							'successful':passes,
							'failed':fails
							})
						print(result[1])
			task_status ='completed'
			msg = f'Task completed, {passes} accounts created'
		except Exception as error:
			print(error)
			task_status ='failed'
			msg = f'Task failed, no accounts created'
		finally:
			try:
				if len(created_accounts) >= 1:
					print('\nCREATING SCHEDULES\n')
					scheduler = Scheduler()
					url = f'https://{SERVER}/start-swipe'
					payload = {'data':{
							'accounts':created_accounts,
							'min_wait':swipe_configs['min_wait'],
							'max_wait':swipe_configs['max_wait'],
							'duration':swipe_configs['swipe_duration'] * 60},
							'schedule':swipe_configs['id'],
							'schedule_name':swipe_configs['name'],
							'session':swipe_configs['session']}
					schedule = self.create_scheduler(scheduler,url,swipe_configs,payload=payload)
					print(f'\n {schedule[1]} \n')
					if schedule[0]:msg += '\n\nSchedule created for successful accounts'
					else: print(schedule[1])
			except Exception as error:
				print(error)
				msg += '\n\nError creating schedule.'

			if passes == 0:task_status ='failed'
			tasks_ref.document(task_id).update({
				'status':task_status,
				'running':False,
				'message':msg,
				'progress':(completed / op_count) * 100,
				'successful':passes,
				'failed':fails
				})
			return success,msg 

	def add_account(self,
      proxies:list = None,
      email: str = None,
      password: str= None,
      url:str = None,
      token:str = None):
		URL = f'{url}/account/login_and_create_account'
		try:
			with httpx.Client(timeout=httpx.Timeout(200.0)) as session:
				session.headers = {
					'Content-Type':'application/json',
					'Authorization': f'Bearer {token}'
				}
				
				json_data = {
					'email': email,
					'password': password,
					'proxies':proxies,
				}

				flow = session.put(URL,json=json_data)
				if flow.status_code > 299:return False,flow.text
				
				print(flow.json())
				account_id = flow.json()['id']
				message = flow.json()['message']
				if account_id is not None:
					flow = session.get(f"{url}/account/{account_id}")
					if flow.status_code  > 299:return False,flow.text,None
					account_details = flow.json()
					account_details['id'] = account_id
					return True,message,account_details
				return True,message,None
		except Exception as error:
			return False,'Adding account failed',error

	def start_add_acccounts(self,
      proxies: str= None,
      accounts_ref=None,
      op_count: int = None,
      tasks_ref=None,
      task_id:str = None,
      max_workers:int = 10,
      email_password_pairs: list = None,
      url:str=None,
      token:str = None):
  
		print('ACCOUNT UPLOAD STARTED')

		already_present,passes,banned,completed,proxy_error= 0,0,0,0,0

		try:
			kwargs=[{
			'proxies': proxies,
			'email': i['email'],
			'password':i['password'],
			'url':url,
			'token':token
			}for i in email_password_pairs]

			with ThreadPoolExecutor(max_workers=max_workers) as executor:
				futures = []
				for kwargs in kwargs:
					future = executor.submit(self.add_account, **kwargs)
					futures.append(future)

				for future in as_completed(futures):
					result = future.result()
					if result[0]:
						msg = result[1]
						completed += 1
						account = result[2]
						if msg == 'already_present':
							already_present+=1
							tasks_ref.document(task_id).update({
							'progress':(completed / op_count) * 100,
							'successful':passes,
							'failed':already_present+banned+proxy_error,
							'already_present':already_present
							})
							continue
						elif msg == 'banned':
							banned+=1
							tasks_ref.document(task_id).update({
							'progress':(completed / op_count) * 100,
							'successful':passes,
							'failed':already_present+banned+proxy_error,
							'banned':banned
							})
							continue
						elif msg == 'proxy_error':
							proxy_error+=1
							tasks_ref.document(task_id).update({
							'progress':(completed / op_count) * 100,
							'successful':passes,
							'failed':already_present+banned+proxy_error,
							'proxy_error':proxy_error
							})
							continue
						else:
							passes += 1
						account['last_updated'] = str(datetime.now())
						accounts_ref.document(account['id']).set(account)
						tasks_ref.document(task_id).update({
							'progress':(completed / op_count) * 100,
							'successful':passes,
							})
				else:
					print(result[1])
					print(result[2])
				task_status ='completed'
				msg = f'task completed, {passes} accounts added'
		except Exception as error:
			import traceback
			print(traceback.format_exc())
			task_status ='failed'
			msg = f'task failed, no accounts added'
		finally:
			if passes == 0: task_status = 'failed'
			tasks_ref.document(task_id).update({
			'status':task_status,
			'running':False,
			'message':msg,
			'successful':passes,
			'failed': already_present+banned+proxy_error
			})
			return msg
