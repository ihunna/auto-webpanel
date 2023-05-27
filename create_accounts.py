from configs import *
from actions import upload_image,verify_phone,login
from utils import generate_sensor_data


def create_accounts(proxies={},password=str,
			fullName=str,bday={},c_code=str,zipcode=str,
			myGender='woman',oGender='men',bioDesc=str,image_count=int):
	time.sleep(random.randint(0,5))
	
	global bearer
	# device_id = '42104318-A2D2-4168-94CA-93049C1EDFF0'
	device_id = str(uuid.uuid4()).upper()
	email = f"{fullName.strip()}@{random.choice(['gmail.com','outlook.com'])}".lower().replace(' ','')
	
	try:
		with httpx.Client(proxies=proxies,verify=False,timeout=20) as session:
			print('\n Getting guest token')
			url = 'https://okcupid.com/graphql'
			session.headers = {
				'content-type': 'application/json',
				'x-okcupid-platform': 'ios',
				'accept': '*/*',
				'apollographql-client-version': '77.0.0-358',
				'x-okcupid-locale': 'en',
				'accept-language': 'en-us',
				'x-okcupid-version': '77.0.0',
				'x-apollo-operation-type': 'query',
				'apollographql-client-name': 'com.okcupid.app-apollo-ios',
				'user-agent': 'OkCupid/358 CFNetwork/1406.0.4 Darwin/22.4.0',
				'x-apollo-operation-name': 'LoggedOutSession',
			}   
			
			json_data = {
				'operationName': 'LoggedOutSession',
				'query': 'query LoggedOutSession($experimentNames: [String]!) {\n  session {\n    __typename\n    isStaff\n    guestId\n    ipCountry\n    shouldUpdateAppDetect\n    isAppsConsentKillswitchEnabled\n    additionalPolicies\n    ...GateKeeperChecksFragment\n    experiments(names: $experimentNames) {\n      __typename\n      group\n    }\n  }\n}\nfragment GateKeeperChecksFragment on Session {\n  __typename\n  gatekeeperChecks {\n    __typename\n    APP_FORCE_UPDATE\n    GDPR_AGE_REDIRECT\n    ONBOARDING_ALLOW_SKIP\n    ONBOARDING_MANDATORY_REDIRECT\n    REBOARDING_MANDATORY_REDIRECT\n    TERMS_MANDATORY_REDIRECT\n    REALNAMES_REDIRECT\n    SMS_MANDATORY_REDIRECT\n    PASSWORD_MANDATORY_REDIRECT\n    BLOCK_PERSONALIZED_MARKETING\n    HAS_PHONE\n    SMS_KILL_SWITCH\n    NEEDS_DETAILS_REBOARDING\n    USE_NEW_INSTAGRAM_API\n    IS_INDIAN_USER\n    GLOBAL_PREFERENCES\n    SUPERLIKES\n    HIDE_INTROS_TAB\n    MARKETING_OPT_IN_NEW_USER\n    IDENTITY_TAGS_QUALIFIES\n    GIF_SEARCH\n    LIVESTREAMING_ALLOWED\n  }\n}',
				'variables': {
					'experimentNames': [
						'CHAT_REACTIONS',
						'CUPIDS_PICKS_V2',
						'IOS_DIRECT_NATIVE_ADS_V2',
						'LIKES_LIST_SORT_V2',
						'IOS_MATCH_EVENT_V1',
						'IOS_NATIVIZE_NAME_LOCATION_V2',
						'PHOTO_MESSAGING',
						'ONBOARDING_GENDER_EDUCATION',
						'RR_PACKAGE_TEST',
						'IOS_NATIVE_SETTINGS_REBOARDING_V3',
						'IOS_RAINN_REPORTING_DEV',
						'SELFIE_VERIFICATION_V1',
						'SENDER_INTERACTION_MECHANICS_IOS_DEV',
						'IOS_CONTENT_CARD_V1',
						'SUPERLIKE_COPY',
						'TEST_EXPERIMENT',
						'TEST_EXPERIMENT_DEV',
						'3_AND_6_MONTH_PRICE_REDUCTION_NEW',
						'TOKEN_PACKAGE_FULL_PRICE',
						'IOS_FAKE_LOGGED_OUT',
						'IOS_UNLIMITED_LIQUIDITY',
						'SUPERLIKE_PACKAGE_TEST',
					],
				},
			}
			
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,'cloudflare blocked'
			guest_token = flow.json()['data']['session']['guestId']
			cf_id = flow.headers['etag']
			print(f'Guest token = {guest_token}\n')

			print(f'\nValidating email: {email}')
			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-name':'ValidateEmail'
				})
			json_data = {
				'operationName': 'ValidateEmail',
				'query': 'query ValidateEmail($email: String!) {\n  auth {\n    __typename\n    isEmailValid(email: $email)\n  }\n}',
				'variables': {
					'email': f'{email}',
				},
			}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			cf_id = flow.headers['etag']
			print(f'Email validation successful: {email}\n')

			print(f'\nValidating password: {password}')
			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-name':'ValidatePassword'
				})
			
			json_data = {
					'operationName': 'ValidatePassword',
					'query': 'query ValidatePassword($password: String!) {\n  auth {\n    __typename\n    isPasswordValid(password: $password)\n  }\n}',
					'variables': {
						'password': f'{password}',
					},
				}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			cf_id = flow.headers['etag']
			print(f'Password validation successful: {password}\n')

			print(f'\nSigning up user: {email}')
			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'SignupWithEmail'
				})
			
			json_data = {
				'operationName': 'SignupWithEmail',
				'query': 'mutation SignupWithEmail($input: AuthUserSignupWithEmailInput!) {\n  authUserSignupWithEmail(input: $input) {\n    __typename\n    success\n    errorCodes\n    user {\n      __typename\n      id\n    }\n  }\n}',
				'variables': {
					'input': {
						'email': f'{email}',
						'password': f'{password}',
					},
				},
			}

			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			cf_id = flow.headers['etag']
			print(f'Sign up successful: {email}\n')
			
			print(f'\n Onboarding user: {email}')
			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'UserUpdateRealname'
				})
			
			json_data = {"operationName":"UserUpdateRealname","query":"mutation UserUpdateRealname($input: UserUpdateRealnameInput!) {\n  userUpdateRealname(input: $input) {\n    __typename\n    success\n    errorCode\n  }\n}","variables":{"input":{"realname":fullName}}}

			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			

			cf_id = flow.headers['etag']
			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'UserUpdateBirthdate'
				})
			
			json_data = {"operationName":"UserUpdateBirthdate","query":"mutation UserUpdateBirthdate($input: UserUpdateBirthdateInput!) {\n  userUpdateBirthdate(input: $input) {\n    __typename\n    success\n    errorCode\n  }\n}","variables":{"input":bday}}

			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			

			session.headers.update({
				"user-agent": 'OKCI 76.1.0 {"id":"iPhone; ; iOS; 16.4.1; iPhone; '+device_id+'","screen":"390.0x844.0x3.0"}',
				"x-okcupid-app": 'OKCI 76.1.0 {"id":"iPhone; ; iOS; 16.4.1; iPhone; '+device_id+'; ; 0","screen":"390.0x844.0x3.0"}'
			})

			flow = session.get(f'https://www.okcupid.com/1/apitun/location/query?country_code={c_code}&q={zipcode}')
			if flow.status_code != 200: return False,flow.text
			locid = flow.json()['results'][0]['locid']

			session.headers = {
				'content-type': 'application/json',
				'x-okcupid-platform': 'ios',
				'accept': '*/*',
				'apollographql-client-version': '77.0.0-358',
				'x-okcupid-locale': 'en',
				'accept-language': 'en-us',
				'x-okcupid-version': '77.0.0',
				'x-apollo-operation-type': 'query',
				'apollographql-client-name': 'com.okcupid.app-apollo-ios',
				'user-agent': 'OkCupid/358 CFNetwork/1406.0.4 Darwin/22.4.0',
				'x-apollo-operation-name': 'LoggedOutSession',
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'UserUpdateLocation'
			}  

			json_data = {"operationName":"UserUpdateLocation","query":"mutation UserUpdateLocation($input: UserUpdateLocationInput!) {\n  userUpdateLocation(input: $input) {\n    __typename\n    success\n    userLocation {\n      __typename\n      id\n      countryCode\n    }\n  }\n}","variables":{"input":{"locid":f"{locid}","postalCode":zipcode}}}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			
			cf_id = flow.headers['etag']
			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'SelfProfileUpdateGenders'
				})
			
			gValue = 0 if myGender == 'woman' else 1
			json_data = {"operationName":"SelfProfileUpdateGenders","query":"mutation SelfProfileUpdateGenders($input: UserUpdateDetailListInput!) {\n  response: userUpdateGenders(input: $input) {\n    __typename\n    success\n    error\n  }\n}","variables":{"input":{"values":[gValue]}}}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text

			

			cf_id = flow.headers['etag']
			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'SetGlobalPreference'
				})
			
			gValue = 0 if oGender == 'woman' else 1
			json_data = {"operationName":"SetGlobalPreference","query":"mutation SetGlobalPreference($input: GlobalPreferencesSetPreferenceInput!) {\n  globalPreferencesSetPreference(input: $input) {\n    __typename\n    success\n    globalPreferences {\n      __typename\n      ...GlobalPreferences\n    }\n  }\n}\nfragment GlobalPreferences on GlobalPreferences {\n  __typename\n  age {\n    __typename\n    values\n    isDealbreaker\n  }\n  bodyType {\n    __typename\n    values\n    isDealbreaker\n  }\n  connectionType {\n    __typename\n    values\n    isDealbreaker\n  }\n  diet {\n    __typename\n    values\n    isDealbreaker\n  }\n  distance {\n    __typename\n    values\n    isDealbreaker\n  }\n  drinking {\n    __typename\n    values\n    isDealbreaker\n  }\n  education {\n    __typename\n    values\n    isDealbreaker\n  }\n  employment {\n    __typename\n    values\n    isDealbreaker\n  }\n  ethnicity {\n    __typename\n    values\n    isDealbreaker\n  }\n  gender {\n    __typename\n    values\n    isDealbreaker\n  }\n  hasKids {\n    __typename\n    values\n    isDealbreaker\n  }\n  height {\n    __typename\n    values\n    isDealbreaker\n  }\n  identityTags {\n    __typename\n    values\n    isDealbreaker\n  }\n  languages {\n    __typename\n    values\n    isDealbreaker\n  }\n  orientation {\n    __typename\n    values\n    isDealbreaker\n  }\n  pets {\n    __typename\n    values\n    isDealbreaker\n  }\n  politics {\n    __typename\n    values\n    isDealbreaker\n  }\n  relationshipStatus {\n    __typename\n    values\n    isDealbreaker\n  }\n  religion {\n    __typename\n    values\n    isDealbreaker\n  }\n  sign {\n    __typename\n    values\n    isDealbreaker\n  }\n  smoking {\n    __typename\n    values\n    isDealbreaker\n  }\n  wantsKids {\n    __typename\n    values\n    isDealbreaker\n  }\n  weed {\n    __typename\n    values\n    isDealbreaker\n  }\n}","variables":{"input":{"preference":"gender","values":[gValue]}}}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text		

			cf_id = flow.headers['etag']
			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'SetGlobalPreference'
				})
			
			json_data = {
				'operationName': 'SetGlobalPreference',
				'query': 'mutation SetGlobalPreference($input: GlobalPreferencesSetPreferenceInput!) {\n  globalPreferencesSetPreference(input: $input) {\n    __typename\n    success\n    globalPreferences {\n      __typename\n      ...GlobalPreferences\n    }\n  }\n}\nfragment GlobalPreferences on GlobalPreferences {\n  __typename\n  age {\n    __typename\n    values\n    isDealbreaker\n  }\n  bodyType {\n    __typename\n    values\n    isDealbreaker\n  }\n  connectionType {\n    __typename\n    values\n    isDealbreaker\n  }\n  diet {\n    __typename\n    values\n    isDealbreaker\n  }\n  distance {\n    __typename\n    values\n    isDealbreaker\n  }\n  drinking {\n    __typename\n    values\n    isDealbreaker\n  }\n  education {\n    __typename\n    values\n    isDealbreaker\n  }\n  employment {\n    __typename\n    values\n    isDealbreaker\n  }\n  ethnicity {\n    __typename\n    values\n    isDealbreaker\n  }\n  gender {\n    __typename\n    values\n    isDealbreaker\n  }\n  hasKids {\n    __typename\n    values\n    isDealbreaker\n  }\n  height {\n    __typename\n    values\n    isDealbreaker\n  }\n  identityTags {\n    __typename\n    values\n    isDealbreaker\n  }\n  languages {\n    __typename\n    values\n    isDealbreaker\n  }\n  orientation {\n    __typename\n    values\n    isDealbreaker\n  }\n  pets {\n    __typename\n    values\n    isDealbreaker\n  }\n  politics {\n    __typename\n    values\n    isDealbreaker\n  }\n  relationshipStatus {\n    __typename\n    values\n    isDealbreaker\n  }\n  religion {\n    __typename\n    values\n    isDealbreaker\n  }\n  sign {\n    __typename\n    values\n    isDealbreaker\n  }\n  smoking {\n    __typename\n    values\n    isDealbreaker\n  }\n  wantsKids {\n    __typename\n    values\n    isDealbreaker\n  }\n  weed {\n    __typename\n    values\n    isDealbreaker\n  }\n}',
				'variables': {
					'input': {
						'preference': 'connectionType',
						'values': [
							1,
							3,
							2,
							6,
						],
					},
				},
			}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text

			

			cf_id = flow.headers['etag']
			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'SetGlobalPreference'
				})
			
			json_data = {
				'operationName': 'SetGlobalPreference',
				'query': 'mutation SetGlobalPreference($input: GlobalPreferencesSetPreferenceInput!) {\n  globalPreferencesSetPreference(input: $input) {\n    __typename\n    success\n    globalPreferences {\n      __typename\n      ...GlobalPreferences\n    }\n  }\n}\nfragment GlobalPreferences on GlobalPreferences {\n  __typename\n  age {\n    __typename\n    values\n    isDealbreaker\n  }\n  bodyType {\n    __typename\n    values\n    isDealbreaker\n  }\n  connectionType {\n    __typename\n    values\n    isDealbreaker\n  }\n  diet {\n    __typename\n    values\n    isDealbreaker\n  }\n  distance {\n    __typename\n    values\n    isDealbreaker\n  }\n  drinking {\n    __typename\n    values\n    isDealbreaker\n  }\n  education {\n    __typename\n    values\n    isDealbreaker\n  }\n  employment {\n    __typename\n    values\n    isDealbreaker\n  }\n  ethnicity {\n    __typename\n    values\n    isDealbreaker\n  }\n  gender {\n    __typename\n    values\n    isDealbreaker\n  }\n  hasKids {\n    __typename\n    values\n    isDealbreaker\n  }\n  height {\n    __typename\n    values\n    isDealbreaker\n  }\n  identityTags {\n    __typename\n    values\n    isDealbreaker\n  }\n  languages {\n    __typename\n    values\n    isDealbreaker\n  }\n  orientation {\n    __typename\n    values\n    isDealbreaker\n  }\n  pets {\n    __typename\n    values\n    isDealbreaker\n  }\n  politics {\n    __typename\n    values\n    isDealbreaker\n  }\n  relationshipStatus {\n    __typename\n    values\n    isDealbreaker\n  }\n  religion {\n    __typename\n    values\n    isDealbreaker\n  }\n  sign {\n    __typename\n    values\n    isDealbreaker\n  }\n  smoking {\n    __typename\n    values\n    isDealbreaker\n  }\n  wantsKids {\n    __typename\n    values\n    isDealbreaker\n  }\n  weed {\n    __typename\n    values\n    isDealbreaker\n  }\n}',
				'variables': {
					'input': {
						'preference': 'age',
						'values': [
							18,
							99,
						],
					},
				},
			}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			
			print(f'\n Uploading images: {email}')
			cookies = dict(session.cookies.items())
			upload = upload_image(
				cookies=cookies,
				proxies=proxies,
				count=image_count,
				device_id=device_id)
			if upload[0]:print(upload[1])
			else: return False,upload[1]
			print(f'\nuploaded {upload[2]} images: {email}')

			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'UpdateEssay'
				})
			
			json_data = {
				'operationName': 'UpdateEssay',
				'query': 'mutation UpdateEssay($input: EssayUpdateInput) {\n  response: essayUpdate(input: $input) {\n    __typename\n    essay {\n      __typename\n      ...ApolloEssay\n    }\n  }\n}\nfragment ApolloEssay on Essay {\n  __typename\n  id\n  title\n  groupTitle\n  groupId\n  isActive\n  isPassion\n  processedContent\n  rawContent\n  placeholder\n  picture {\n    __typename\n    id\n    square800\n  }\n}',
				'variables': {
					'input': {
						'essayContent': bioDesc,
						'essayId': f'{guest_token}-essay-0',
						'groupId': '0',
					},
				},
			}

			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			
			count = 0
			print('\nAnswering questions')
			answers = []
			while count < 15:
				session.headers.update({
					'if-none-match': f'{cf_id}',
					'x-apollo-operation-type': 'mutation',
					'x-apollo-operation-name':'NextQuestion'
					})
				
				json_data = {
					'operationName': 'NextQuestion',
					'query': 'query NextQuestion($source: QuestionSource!) {\n  me {\n    __typename\n    nextQuestion(source: $source) {\n      __typename\n      id\n      text\n      answers\n    }\n  }\n}',
					'variables': {
						'source': 'ONBOARDING',
					},
				}

				time.sleep(random.randint(0,5))
				flow = session.post(url,json=json_data)
				if flow.status_code != 200: return False,flow.text
				
				ans = flow.json()['data']['me']['nextQuestion']
				ans_id = ans['id']
				chosen_ans = random.randint(0,len(ans['answers'])-1)
				answers.append(chosen_ans)
				print(f'\nQuestion {count+1}')
				print(f'{ans["text"]}: {ans["answers"][chosen_ans]}')
				session.headers.update({
					'if-none-match': f'{cf_id}',
					'x-apollo-operation-type': 'mutation',
					'x-apollo-operation-name':'QuestionsQuestionAnswer'
					})
				
				json_data = {
					'operationName': 'QuestionsQuestionAnswer',
					'query': 'mutation QuestionsQuestionAnswer($input: QuestionsQuestionAnswerInput!) {\n  questionsQuestionAnswer(input: $input) {\n    __typename\n    success\n    nextQuestion {\n      __typename\n      id\n      text\n      answers\n    }\n  }\n}',
					'variables': {
						'input': {
							'answer': chosen_ans,
							'id': ans_id,
							'matchAnswers': [
								chosen_ans,
							],
							'shouldGetNextQuestion': True,
							'source': 'ONBOARDING',
						},
					},
				}

				time.sleep(random.randint(0,5))
				flow = session.post(url,json=json_data)
				if flow.status_code != 200: return False,flow.text

				count += 1

			print('\n Getting phone number')
			time.sleep(random.randint(5,10))

			verify_phone(action='auth')
			phone = verify_phone(action='get_number')
			assert phone[0] == True
			phone = phone[1]

			print(f'Phone number = {phone["number"]}\n')

			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'CreateAuthAccessToken'
				})
			
			json_data = {
				'operationName': 'CreateAuthAccessToken',
				'query': 'mutation CreateAuthAccessToken {\n  authTSPAccessTokenCreate {\n    __typename\n    tspAccessToken\n  }\n}',
				'variables': None,
			}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text

			token = flow.json()['data']['authTSPAccessTokenCreate']['tspAccessToken']


			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'SendPhoneNumber'
				})
			
			json_data = {
				'operationName': 'SendPhoneNumber',
				'query': 'mutation SendPhoneNumber($input: AuthOTPSendInput!) {\n  authOTPSend(input: $input) {\n    __typename\n    success\n    statusCode\n  }\n}',
				'variables': {
					'input': {
						'phoneNumber': f'+1{phone["number"]}',
						'platform': 'IOS',
						'smsFlow': 'ONBOARDING',
						'tspAccessToken': f'{token}',
					},
				},
			}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text


			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'CreateAuthAccessToken'
				})
			
			json_data = {
				'operationName': 'CreateAuthAccessToken',
				'query': 'mutation CreateAuthAccessToken {\n  authTSPAccessTokenCreate {\n    __typename\n    tspAccessToken\n  }\n}',
				'variables': None,
			}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text

			token = flow.json()['data']['authTSPAccessTokenCreate']['tspAccessToken']

			status = 'Pending'
			print('\n Checking for OTP')
			while status == 'Pending':
				time.sleep(random.randint(10,20))
				otp = verify_phone(action='get_code',phone=phone)
				assert otp [0] == True
				otp = otp[1]
				status = otp['status']
			print(f'OTP = {otp["code"]}\n')

			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'SendVerificationCode'
				})
			json_data = {
				'operationName': 'SendVerificationCode',
				'query': 'mutation SendVerificationCode($input: AuthTSPRefreshTokenCreateInput!) {\n  authTSPRefreshTokenCreate(input: $input) {\n    __typename\n    tspRefreshToken\n  }\n}',
				'variables': {
					'input': {
						'otp': f'{otp["code"]}',
						'phoneNumber': f'+1{phone["number"]}',
						'platform': 'IOS',
						'tspAccessToken': f'{token}',
					},
				},
			}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			r_token = flow.json()['data']['authTSPRefreshTokenCreate']['tspRefreshToken']
			

			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'UpdatePhoneNumber'
				})
			json_data = {
				'operationName': 'UpdatePhoneNumber',
				'query': 'mutation UpdatePhoneNumber($input: UserUpdatePhoneNumberInput!) {\n  userUpdatePhoneNumber(input: $input) {\n    __typename\n    success\n    statusCode\n  }\n}',
				'variables': {
					'input': {
						'tspRefreshToken': f'{r_token}',
					},
				},
			}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text


			session.headers.update({
				'if-none-match': f'{cf_id}',
				'x-apollo-operation-type': 'mutation',
				'x-apollo-operation-name':'OnboardingFinish'
				})
			
			json_data = {
				'operationName': 'OnboardingFinish',
				'query': 'mutation OnboardingFinish($input: OnboardingFinishInput!) {\n  onboardingFinish(input: $input) {\n    __typename\n    success\n  }\n}',
				'variables': {
					'input': {
						'configName': 'ONBOARDING_FUNNEL_WITH_PHONE',
						'isReboarding': False,
						'markNonMonogamy': False,
					},
				},
			}
			time.sleep(random.randint(0,5))
			flow = session.post(url,json=json_data)
			if flow.status_code != 200: return False,flow.text
			print(f'\nOnboarding finished: {email}')

			user = {
				'ip': proxies,
				'cookies':dict(session.cookies.items()),
				'headers':dict(session.headers.items()),
				'device-id':device_id,
				'email':email,
				'password':password,
				'phone':otp,
				'bio':bioDesc,
				'answers':answers

			}
			session.headers.update({'x-apollo-operation-name': 'LoginWithEmail'})
			json_data = {
				'operationName': 'LoginWithEmail',
				'query': 'mutation LoginWithEmail($input: AuthUserLoginWithEmailInput!) {\n  authUserLoginWithEmail(input: $input) {\n    __typename\n    userid\n    statusCode\n    reenableAuthCode\n    reenableUserid\n    onboardingIncomplete\n  }\n}',
				'variables': {
					'input': {
						'authCode': None,
						'deviceId': user['device-id'],
						'email': user['email'],
						'password': user['password'],
					},
				},
			}

			flow = session.post('https://okcupid.com/graphql',json=json_data)
			if flow.status_code != 200:return False,flow.text
			cf_id = flow.headers['etag']

			if 'connection' in session.headers.keys():session.headers.pop('connection')
			session.headers.update({
				'accept': '*/*',
				'x-apollo-operation-type': 'query',
				'x-apollo-operation-name': 'LikesCapInfo',
				'if-none-match': cf_id,
			})

			json_data = {
				'operationName': 'LikesCapInfo',
				'query': 'query LikesCapInfo {\n  me {\n    __typename\n    likesCap {\n      __typename\n      ...LikesCapFragment\n    }\n  }\n}\nfragment LikesCapFragment on LikesCap {\n  __typename\n  likesCapTotal\n  likesRemaining\n  viewCount\n  resetTime\n}',
				'variables': None,
			}

			# session.cookies.update({
			# 	'secure_login':'0',
			# 	'secure_check':'0'
			# })

			flow = session.post('https://okcupid.com/graphql',json=json_data)
			if flow.status_code != 200:return False,flow.text
			cf_id = flow.headers['etag']


			session.headers.update({
				'x-apollo-operation-name': 'StacksSessionQuery',
				'if-none-match': cf_id,
			})
			json_data = {
				'operationName': 'StacksSessionQuery',
				'query': 'query StacksSessionQuery($experimentNames: [String]!) {\n  session {\n    __typename\n    isStaff\n    guestId\n    ipCountry\n    shouldUpdateAppDetect\n    isAppsConsentKillswitchEnabled\n    additionalPolicies\n    ...GateKeeperChecksFragment\n    experiments(names: $experimentNames) {\n      __typename\n      group\n    }\n  }\n  me {\n    __typename\n    id\n    displayname\n    emailAddress\n    username\n    realname\n    age\n    binaryGenderLetter\n    orientations\n    relationshipType\n    unitPreference\n    userLocation {\n      __typename\n      publicName\n    }\n    ...NotificationsFragment\n    isOnline\n    hasInstagram\n    boostTokenCount\n    readReceiptTokenCount\n    stackPassTokenCount\n    superlikeTokenCount\n    rewindTokenCount\n    hasMetPhotoRequirements\n    hasSeenSwipingTutorial: hasSeenUserGuide(feature: USER_SWIPING_TUTORIAL)\n    hasSeenIdentityTagsDiscoverabilityModal: hasSeenUserGuide(\n      feature: IDENTITY_TAGS\n    )\n    joinDate\n    primaryImage {\n      __typename\n      square800\n    }\n    ...ApolloNotificationCounts\n    ...SubscriptionInfo\n    globalPreferences {\n      __typename\n      gender {\n        __typename\n        values\n      }\n    }\n    selfieVerifiedStatus(shouldReturnStatus: true)\n    stack(\n      id: JUST_FOR_YOU\n      excludedUserIds: []\n      shouldReturnStatusForSelfieVerification: true\n    ) {\n      __typename\n      ...DoubleTakeStack\n    }\n  }\n}\nfragment GateKeeperChecksFragment on Session {\n  __typename\n  gatekeeperChecks {\n    __typename\n    APP_FORCE_UPDATE\n    GDPR_AGE_REDIRECT\n    ONBOARDING_ALLOW_SKIP\n    ONBOARDING_MANDATORY_REDIRECT\n    REBOARDING_MANDATORY_REDIRECT\n    TERMS_MANDATORY_REDIRECT\n    REALNAMES_REDIRECT\n    SMS_MANDATORY_REDIRECT\n    PASSWORD_MANDATORY_REDIRECT\n    BLOCK_PERSONALIZED_MARKETING\n    HAS_PHONE\n    SMS_KILL_SWITCH\n    NEEDS_DETAILS_REBOARDING\n    USE_NEW_INSTAGRAM_API\n    IS_INDIAN_USER\n    GLOBAL_PREFERENCES\n    SUPERLIKES\n    HIDE_INTROS_TAB\n    MARKETING_OPT_IN_NEW_USER\n    IDENTITY_TAGS_QUALIFIES\n    GIF_SEARCH\n    LIVESTREAMING_ALLOWED\n  }\n}\nfragment NotificationsFragment on User {\n  __typename\n  notifications {\n    __typename\n    type\n    title\n    subtitle\n    redirectPathURL\n    target {\n      __typename\n      ...ApolloIntroUser\n      ...ApolloPreviewUser\n    }\n    isViaSpotlight\n  }\n}\nfragment ApolloIntroUser on Match {\n  __typename\n  firstMessage {\n    __typename\n    text\n    id\n  }\n  user {\n    __typename\n    primaryImage {\n      __typename\n      square800\n    }\n  }\n  ...ApolloBaseUser\n}\nfragment ApolloBaseUser on Match {\n  __typename\n  user {\n    __typename\n    id\n    username\n    displayname\n    age\n    userLocation {\n      __typename\n      publicName\n    }\n    primaryImage {\n      __typename\n      square800\n    }\n    isOnline\n  }\n  matchPercent\n  senderVote\n  targetVote\n  targetLikes\n  likeTime\n  targetLikeViaSpotlight\n  targetLikeViaSuperBoost\n  targetMessageTime\n  firstMessage {\n    __typename\n    text\n    time\n    threadId\n    attachments {\n      __typename\n      ... on ProfileCommentPhoto {\n        __typename\n        photo {\n          __typename\n          id\n          original\n        }\n      }\n      ... on ProfileCommentInstagramPhoto {\n        __typename\n        instagramPhoto {\n          __typename\n          id\n          original\n        }\n      }\n      ... on ProfileCommentEssay {\n        __typename\n        essayText\n      }\n    }\n  }\n}\nfragment ApolloPreviewUser on MatchPreview {\n  __typename\n  primaryImageBlurred {\n    __typename\n    square800\n  }\n  hasFirstMessage\n  targetSuperlikes\n}\nfragment ApolloNotificationCounts on User {\n  __typename\n  notificationCounts {\n    __typename\n    messages\n    likesIncoming\n    likesMutual\n    intros\n  }\n}\nfragment SubscriptionInfo on User {\n  __typename\n  unlimitedLikesSubscriptionFeature: featureSubscription(feature: UNLIMITED_LIKES) {\n    __typename\n    ...SubscriptionFeature\n  }\n  seeWhoLikesYouSubscriptionFeature: featureSubscription(\n    feature: SEE_WHO_LIKES_YOU\n  ) {\n    __typename\n    ...SubscriptionFeature\n  }\n  ALIST_BASIC: hasPremium(name: ALIST_BASIC)\n  ALIST_PREMIUM: hasPremium(name: ALIST_PREMIUM)\n  INCOGNITO: hasPremium(name: INCOGNITO_BUNDLE)\n}\nfragment SubscriptionFeature on FeatureSubscription {\n  __typename\n  timeOfActualLoss\n  wasEverActive\n  isActive\n}\nfragment DoubleTakeStack on Stack {\n  __typename\n  id\n  expireTime\n  status\n  emptyStateStatus\n  votesRemaining\n  badge\n  data {\n    __typename\n    ... on StackMatch {\n      __typename\n      stream\n      targetLikesSender\n      hasSuperlikeRecommendation\n      profileHighlights {\n        __typename\n        ...Highlight\n      }\n      selfieVerifiedStatus\n      match {\n        __typename\n        ...ApolloBaseUser\n        user {\n          __typename\n          userLocation {\n            __typename\n            countryCode\n          }\n          essaysWithUniqueIds {\n            __typename\n            id\n            title\n            processedContent\n            placeholder\n            picture {\n              __typename\n              id\n              original\n              square800\n            }\n          }\n          occupation {\n            __typename\n            title\n            employer\n          }\n          education {\n            __typename\n            level\n            school {\n              __typename\n              id\n              name\n            }\n          }\n          photos {\n            __typename\n            id\n            caption\n            width\n            height\n            crop {\n              __typename\n              upperLeftX\n              upperLeftY\n              lowerRightX\n              lowerRightY\n            }\n            original\n            square800\n          }\n        }\n      }\n    }\n    ... on FirstPartyAd {\n      __typename\n      id\n    }\n    ... on ThirdPartyAd {\n      __typename\n      ad\n    }\n    ... on PromotedQuestionPrompt {\n      __typename\n      promotedQuestionId\n    }\n  }\n}\nfragment Highlight on ProfileHighlight {\n  __typename\n  ... on PhotoHighlight {\n    __typename\n    id\n    url\n    caption\n  }\n  ... on QuestionHighlight {\n    __typename\n    id\n    question\n    answer\n    explanation\n  }\n}',
				'variables': {
					'experimentNames': [
						'CHAT_REACTIONS',
						'CUPIDS_PICKS_V2',
						'IOS_DIRECT_NATIVE_ADS_V2',
						'LIKES_LIST_SORT_V2',
						'IOS_MATCH_EVENT_V1',
						'IOS_NATIVIZE_NAME_LOCATION_V2',
						'PHOTO_MESSAGING',
						'ONBOARDING_GENDER_EDUCATION',
						'RR_PACKAGE_TEST',
						'IOS_NATIVE_SETTINGS_REBOARDING_V3',
						'IOS_RAINN_REPORTING_DEV',
						'SELFIE_VERIFICATION_V1',
						'SENDER_INTERACTION_MECHANICS_IOS_DEV',
						'IOS_CONTENT_CARD_V1',
						'SUPERLIKE_COPY',
						'TEST_EXPERIMENT',
						'TEST_EXPERIMENT_DEV',
						'3_AND_6_MONTH_PRICE_REDUCTION_NEW',
						'TOKEN_PACKAGE_FULL_PRICE',
						'IOS_FAKE_LOGGED_OUT',
						'IOS_UNLIMITED_LIQUIDITY',
						'SUPERLIKE_PACKAGE_TEST',
					],
				},
			}

			# session.cookies.update({
			# 	'secure_login':'0',
			# 	'secure_check':'0'
			# })

			flow = session.post('https://okcupid.com/graphql',json=json_data)
			if flow.status_code != 200:return False,flow.text
			cf_id = flow.headers['etag']

			user['cookies'] = dict(flow.cookies.items())
			user['headers'] = dict(session.headers.items())
			user['user_data'] = flow.json()
			user['id'] = guest_token

			print(f'\nAccount creation successful: {email}\n')

			return True,user
	except Exception as error:
		print(error)
		return False,error


if __name__ == "__main__":
	"""
	This is not at the optimal stage yet but everything works for now.
	More functionalites to be added.
	"""

	print("enter accounts bio")
	bio = input("enter accounts bio description: ").strip().lower()
	while bio == '':
		bio = input("please enter enter accounts bio description: ").strip().lower()

	max_workers = input("\nEnter limit: ").strip()
	while max_workers == "" or not max_workers.isdigit():
		max_workers = input("Enter limit count: ").strip()
	max_workers = int(max_workers)
	
	names = []
	zipcodes = []
	with open('names.txt','r') as n_f:
		names += n_f.readlines()

	with open('zipcodes.txt','r') as n_f:
		zipcodes += n_f.readlines()

	proxies = [proxies[i] for i in range(max_workers)]

	kwargs=[{
		'proxies':proxy,
		'password':generate_sensor_data(type='password'),
		'fullName': f'{random.choice(names)} {random.choice(names)}'.replace('\n',''),
		'bday':{"day":random.randint(1,30),"month":random.randint(1,12),"year":random.randint(1980,2005)},
		'c_code':'US',
		'zipcode':f'{random.choice(zipcodes)}'.strip().replace('\n',''),
		'bioDesc':bio,
		'image_count':2

	}for proxy in proxies]

	with ThreadPoolExecutor(max_workers=2) as executor:

		futures = []
		for kwargs in kwargs:
			future = executor.submit(create_accounts, **kwargs)
			futures.append(future)

		for future in as_completed(futures):
			user = future.result()
			if user[0]:
				with open('accounts.json','r+',encoding='utf-8') as users_file:
					users = json.load(users_file)
					users[user[1]['id']] = user[1]
					users_file.seek(0)
					json.dump(users,users_file,ensure_ascii=False,indent=4,default=str)
			else:print(user[1])


