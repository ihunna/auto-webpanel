from app_configs import httpx,SearchEngine,time,random,ThreadPoolExecutor,as_completed,json,firestore





def get_location(zipcode):
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

def create_accounts(
			account:int =None,
			nb_of_images:int=5,
			nb_of_accounts:int = 1,
			names:list=None,
			handles:list=None,
			bios:list = None,
			task_id:str = None,
			profile_images:list = None,
			verification_images:dict = None,
			age_range:str = '18-60',
			gender:str = None,
			cities:list = None,
			proxies:list = None,
			user_agents:list = None,
			accounts:list = None,
			url:str = None,
			token:str = None):
	URL = f'{url}/account'
	try:
		with httpx.Client() as session:
			session.headers = {
				'Content-Type':'application/json',
				'Authorization': f'Bearer {token}'
			}
			
			json_data = {
				'nb_of_accounts':nb_of_accounts,
				'names':names,
				'bios':bios,
				'handles':handles,
				'profile_images':profile_images,
				"nb_of_images":nb_of_images,
				'verification_images':verification_images,
				'age-range':age_range,
				'gender':gender,
				'cities':cities,
				'proxies':proxies,
				'user_agents':user_agents,
				'accounts':accounts,
			}

			flow = session.put(URL,json=json_data)
			if flow.status_code > 299:return False,flow.text
			
			print(f'\nWaiting for account to be created for: {account + 1}')
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

def start_task(
			accounts_ref=None,
			tasks_ref=None,
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
			cities:list = None,
			proxies:list = None,
			user_agents:list = None,
			accounts:list = None,
			url:str=None,
			token:str = None):
	
	print('\nACCOUNT CREATION STARTED \n')
	success,msg,task_status = False,'',''
	fails,passes,completed= 0,0,0

	try:
		kwargs=[{
			'account':i,
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
			'profile_images':images,
			'nb_of_images':nb_of_images,
			'verification_images':verification_images,
			'url':url,
			'token':token
		}for i in range(op_count)]

		with ThreadPoolExecutor(max_workers=max_workers) as executor:
			futures = []
			for kwargs in kwargs:
				future = executor.submit(create_accounts, **kwargs)
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
					account['profile'] = json.dumps(account['profile'])
					accounts_ref.document(account['id']).set(account)
					
					passes += 1
					msg = f'{passes} account of {op_count} created successfully and {op_count - (passes+fails)} waiting to be created'
					tasks_ref.document(task_id).update({
						'message':msg,
						'progress':(completed / op_count) * 100,
						'successful':passes,
						'failed':fails
						})
					
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
		msg = f'account creation completed, {passes} accounts created'
	except Exception as error:
		print(error)
		task_status ='failed'
		msg = f'account creation failed, no accounts created'
	finally:
		tasks_ref.document(task_id).update({
			'status':task_status,
			'running':False,
			'message':msg,
			'progress':(completed / op_count) * 100,
			'successful':passes,
			'failed':fails
			})
		return success,msg 