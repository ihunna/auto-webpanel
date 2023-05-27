from app_configs import uuid,names_file,zip_file,httpx,SearchEngine,sqlite3,database_file,time
from configs import random,ThreadPoolExecutor,as_completed,json
from utils import generate_sensor_data




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
		fullName:str = None,
		password:str = None,
		bio:str = None,
		bday:dict = None,
		c_code:str = None,
		zipcode:str = None,
		image:dict = None,
		token:str | dict = None):
	URL = 'https://okcupid-api.uc.r.appspot.com/account'
	try:
		email = email = f"{fullName.strip()}@{random.choice(['gmail.com','outlook.com'])}".lower().replace(' ','')
		with httpx.Client() as session:
			session.headers = {
				'Content-Type':'application/json',
				'Authorization': f'Bearer {token}'
			}
			
			location = get_location(zipcode)
			if not location[0]:return False, location[1]
			location = location[1]
			json_data = {
				"email": email,
				"password":password,
				"name": fullName,
				"birth_date": bday,
				"country_code": c_code,
				"region": location['state'],
				"city": location['city'],
				"zipcode": zipcode,
				"area_code": location['area_code'],
				"gender": 0,
				"gender_preferences": [1],
				"connection_types": [1, 3, 2, 6],
				"age_range": [18, 99],
				"bio_description": bio,
				"device_id": str(uuid.uuid4()).upper(),
				"image_urls": image['links']
			}

			flow = session.post(URL,json=json_data)
			if flow.status_code != 200:return False,flow.text
			
			print(f'\nWaiting for account to be created for: {email}')
			status = 'PENDING_CREATION'
			account_id = flow.json().get('account_id')
			while status == 'PENDING_CREATION':
				flow = session.get(f"https://okcupid-api.uc.r.appspot.com/account/{account_id}")
				if flow.status_code != 200:return False,flow.text
				status = flow.json().get('status')
				time.sleep(10)
			return True,flow.json()

	except Exception as error:
		return False,error

def start_task(
		op_count:int=None,
		max_workers:int=None,
		bio:str=None,
		images:list=None,
		task_id:str=None,
		token:str | dict = None):
	
	print('\nACCOUNT CREATION STARTED \n')

	db = sqlite3.connect(database_file)
	global account_task_status
	success,msg = False,''
	try:
		names = []
		zipcodes = []
		with open(names_file,'r') as n_f:
			names += n_f.readlines()

		with open(zip_file,'r') as n_f:
			zipcodes += n_f.readlines()

		kwargs=[{
			'password':generate_sensor_data(type='password'),
			'fullName': f'{random.choice(names)} {random.choice(names)}'.replace('\n',''),
			'bday':{"day":random.randint(1,30),"month":random.randint(1,12),"year":random.randint(1980,2005)},
			'c_code':'US',
			'zipcode':f'{random.choice(zipcodes)}'.strip().replace('\n',''),
			'bio':bio,
			'image':images[i],
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
					print(account)
					if account.get('status') == 'CREATION_ERROR':
						account_task_status = 'Failed'
						success,msg = True,'Some accounts failed'
						continue
					account_id = account['data']['authUserLoginWithEmail']['userid']
					cursor.execute('''
					INSERT INTO accounts (id,data,email,swipes,messages,likes) VALUES (?,?,?,?,?,?)
					''',(account_id,json.dumps(account),account.get('email'),0,0,0))

					account_task_status = 'Completed'
					success,msg = True,'Account creation successful'
					
				else:print(result[1])
	except Exception as error:
		success,msg = False,error
		print(error)
		account_task_status = 'Failed'
	finally:
		cursor = db.cursor()
		cursor.execute('''UPDATE tasks SET status =? WHERE id =?''',(account_task_status,task_id))
		db.commit()

		return success,msg 