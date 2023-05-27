from configs import *
from utils import time_diff

def upload_image(image_folder=img_folder,headers={},cookies={},proxies={},count=2,i=0,device_id=str):
	try:
		"""
		We are randomly selecting images for now and only image is uploaded
		"""
		images = [image for image in listdir(image_folder) if isfile(f"{image_folder}/{image}")]

		for img_name in images:
			if count < 1:break
			image_path = f'{image_folder}/{img_name}'
			width, height = Image.open(image_path).size
			tn_lower_right_x, tn_lower_right_y = (width, height)

			files = {'file': ('ipodfile.jpg', open(image_path, 'rb'), 'application/octate-stream')}

			data = {
				'commit':'commit',
				'okc_api':'1',
				'tn_upper_left_x':'0',
				'tn_upper_left_y':'0',
				'tn_lower_right_x':tn_lower_right_x,
				'tn_lower_right_y':tn_lower_right_y,
				'status':'0',
				'type':'1'
				}
			
			headers = {
				"accept": "application/json",
				"x-okcupid-locale": "en",
				"x-okcupid-app": 'OKCI 77.0.0 {"id":"iPhone; ; iOS; 16.4.1; iPhone; '+device_id+'; ; 0","screen":"390.0x844.0x3.0"}',
				"accept-language": "en-us",
				"accept-encoding": "br, gzip, deflate",
				"user-agent": 'OKCI 77.0.0 {"id":"iPhone; ; iOS; 16.4.1; iPhone; '+device_id+'","screen":"390.0x844.0x3.0"}',
			}
					
			
			flow = httpx.post('https://www.okcupid.com/ajaxuploader',
				headers=headers,
				cookies=cookies,
				proxies=proxies,
				files=files,
				data=data,
				verify=False,
				timeout=30)
			if flow.status_code == httpx.codes.OK:i+=1
			count -= 1

		if i > 0:return True,'image uploaded successfully',i
		else:return False, 'image upload error', i
	except Exception as error:
		return False, error,i

def verify_phone(action='auth',phone={'id':''}):
	global bearer
	try:
		if action == 'auth':
			now = int(time.time() * 1e9)
			old_time = bearer['ticks']
			if now - old_time > 0:
				bearer = httpx.post('https://www.textverified.com/Api/SimpleAuthentication',
				headers={'X-SIMPLE-API-ACCESS-TOKEN':api_key})
				if bearer.status_code != 200:return False, bearer.text
				bearer = bearer.json()
				return True, bearer
			return True,bearer
		elif action == 'get_number':
			target = httpx.post(
				'https://www.textverified.com/api/Verifications',
				headers={
					'content-type':'application/json',
					'Authorization':f'Bearer {bearer["bearer_token"]}'},
				json={'id':353})
			if target.status_code != 200:return False, target.text
			return True, target.json()
		
		elif action == 'get_code':
			code = httpx.get(
				f'https://www.textverified.com/api/Verifications/{phone["id"]}',
				headers={
					'content-type':'application/json',
					'Authorization':f'Bearer {bearer["bearer_token"]}'})
			
			if code.status_code != 200:return False, code.text,code
			return True, code.json()

	except Exception as error:
		return False, error

def login(user):
	try:
		with httpx.Client(proxies=user['ip'],verify=False,timeout=20) as session:
			headers = user['headers']
			headers.update({'x-apollo-operation-name': 'LoginWithEmail'})

			cookies = user['cookies']

			session.headers.update(headers)
			# session.cookies.update(cookies)

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
				#'if-none-match': cf_id,
			})

			session.cookies.update({
				'secure_check':'0',
				'secure_login':'0'
			})

			json_data = {
				'operationName': 'LikesCapInfo',
				'query': 'query LikesCapInfo {\n  me {\n    __typename\n    likesCap {\n      __typename\n      ...LikesCapFragment\n    }\n  }\n}\nfragment LikesCapFragment on LikesCap {\n  __typename\n  likesCapTotal\n  likesRemaining\n  viewCount\n  resetTime\n}',
				'variables': None,
			}

			flow = session.post('https://okcupid.com/graphql',json=json_data)
			if flow.status_code != 200:return False,flow.text
			cf_id = flow.headers['etag']


			session.headers.update({
				'x-apollo-operation-name': 'StacksSessionQuery',
				#'if-none-match': cf_id,
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
			flow = session.post('https://okcupid.com/graphql',json=json_data)
			if flow.status_code != 200:return False,flow.text
			cf_id = flow.headers['etag']

			user['cookies'] = dict(flow.cookies.items())
			user['headers'] = dict(session.headers.items())
			user['user_data'] = flow.json()
			return True,user
	except Exception as error:
		return False,error