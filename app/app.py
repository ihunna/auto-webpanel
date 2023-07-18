from app_configs import *
from app_utils import create_edit_menu,share_daily_percent,get_image_from_gdrive,check_proxies_format
from app_actions import TASKS
from scheduler import Scheduler


'''
Swipe,send msg pages not implemented yet.
Account creation implemented to some degree as I'm unable to get a better data from
the other server.
Role/admin and some front-end fucntionalities not implemented yet 
as I'm more focused on the account creation for now.


Once account creation is working, I'd be focused on other things, except if you want me to shift focus.
'''
@app.before_request
def before_request():
	g.admin =  session.get('ADMIN')
	g.model = session.get('MODEL')
	g.platform = session.get('PLATFORM')
	g.passkey = app.config['PASS_KEY']
	g.secret_link = app.config['S_LINK']
	g.gcloudkey = app.config['GCLOUDKEY']

@app.after_request
def after_request(response):
	"""Ensure responses aren't cached"""
	response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
	response.headers["Expires"] = 0
	response.headers["Pragma"] = "no-cache"
	return response


@app.route('/')
def serve_lander():
	return render_template('lander.html')


@app.route('/dashboard')
@login_required
@blocked
def redirect_dash():
	return redirect('/platforms')

@app.route('/admins', methods=['GET'])
@login_required
@blocked
def admins():
	g.page = 'admins'
	action = request.args.get('action')

	if action and action == 'admin-settings':
		admin = session.get('ADMIN')
		admin_id = admin['id']

		admin_doc = app.config['ADMINS_REF'].document(admin_id).get().to_dict()

		admin_images = admin_doc.get('images_count', 0)
		admin_accounts = admin_doc.get('accounts_count', 0)
		admin_tasks = admin_doc.get('tasks_count', 0)

		return render_template('admins.html', action=action, admin=admin,
							   admin_images=admin_images, admin_accounts=admin_accounts, admin_tasks=admin_tasks)

	elif action and action == 'edit-signup-configs':
		admin = session.get('ADMIN')
		return render_template('admins.html', action=action, admin=admin)

	if session['ADMIN']['role'] != 'admin':
		page = int(request.args.get('page', 1))
		limit = int(request.args.get('limit', 20))

		admins_ref = app.config['ADMINS_REF']
		total = admins_ref.get().__len__()

		offset = (page - 1) * limit if page <= total else 0

		admins_query = admins_ref.order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit).offset(offset).get()

		admins = [admin_doc.to_dict() for admin_doc in admins_query]

		for admin in admins:
			app.config['ADMINS'].update({admin['id']: admin})

		admin_id = session.get('ADMIN')['id']
		session['ADMIN'] = app.config['ADMINS'][admin_id]

		sum = min((offset) + len(admins), total)
		return render_template('admins.html', admins=admins, page=page, sum=sum, limit=limit, total=total)

	return redirect(url_for('admins', admin=session['ADMIN']['id'], action='admin-settings'))

@app.route('/admins/<action>', methods=['POST'])
@login_required
@blocked
def admin(action):
	try:
		admin = session.get('ADMIN')
		
		if action == 'admin-settings':
			full_name = request.form.get('admin-fullname')
			email = request.form.get('admin-email')
			emails = [e.get('email') for e in app.config['ADMINS_REF'].get()]

			admin_id = session.get('ADMIN')['id']

			if email not in emails:
				app.config['ADMINS_REF'].document(admin_id).update({
					'full_name': full_name,
					'email': email
				})
			else:
				app.config['ADMINS_REF'].document(admin_id).update({
					'full_name': full_name
				})

			return jsonify({'msg': 'Admin updated successfully'}), 200

		elif action == 'make-super':
			op_admin_id = request.get_json()['data'][0]['id']
			op_admin = app.config['ADMINS_REF'].document(op_admin_id).get().to_dict()
			op_admin_status = op_admin.get('status')

			if (admin['role'] == 'super-admin' and op_admin_status == 'active') and admin['id'] != op_admin_id:
				app.config['ADMINS_REF'].document(op_admin_id).update({
					'role': 'super-admin'
				})

				return jsonify({'msg': 'User updated to super admin'}), 200

			return jsonify({'msg': 'Unauthorized'}), 403

		elif action == 'block':
			op_admin_id = request.get_json()['data'][0]['id']
			op_admin = app.config['ADMINS_REF'].document(op_admin_id).get().to_dict()
			op_admin_status = op_admin.get('status')

			if (admin['role'] == 'super-admin' and op_admin_status == 'active') and admin['id'] != op_admin_id:
				app.config['ADMINS_REF'].document(op_admin_id).update({
					'status': 'blocked',
					'role': 'admin'
				})

				return jsonify({'msg': 'User blocked'}), 200

			return jsonify({'msg': 'Unauthorized'}), 403

		elif action == 'unblock':
			op_admin_id = request.get_json()['data'][0]['id']
			op_admin = app.config['ADMINS_REF'].document(op_admin_id).get().to_dict()
			op_admin_status = op_admin.get('status')

			if (admin['role'] == 'super-admin' and op_admin_status == 'blocked') and admin['id'] != op_admin_id:
				app.config['ADMINS_REF'].document(op_admin_id).update({
					'status': 'active'
				})

				return jsonify({'msg': 'User unblocked'}), 200

			return jsonify({'msg': 'Unauthorized'}), 403
		
		elif action == 'login-as-user':
			op_admin_id = request.get_json()['data'][0]['id']
			op_admin = app.config['ADMINS_REF'].document(op_admin_id).get().to_dict()
			op_admin_status = op_admin.get('status')
			op_admin_role = op_admin.get('role')

			if (admin['role'] == 'super-admin' and op_admin_status == 'active') and op_admin_role != 'super-admin':
				if logout():
					session['ADMIN'] = app.config['ADMINS'][op_admin_id]
					session['PLATFORMS'] = {}
					session['MODELS'] = {} 
					response = make_response(jsonify({'msg': f"Logged in as {session['ADMIN']['full_name']}"}),200)
					response.delete_cookie('session')
					return response
				jsonify({'msg': f"couldn't log you in as user"}, 400)
			return jsonify({'msg': 'Unauthorized'}), 403 
		
		elif action == 'delete-user':
			op_admin_id = request.get_json()['data'][0]['id']
			op_admin = app.config['ADMINS_REF'].document(op_admin_id).get().to_dict()
			op_admin_status = op_admin.get('status')
			op_admin_role = op_admin.get('role')

			admin = session.get('ADMIN')

			if (admin['role'] == 'super-admin' and admin['id'] != op_admin_id) and op_admin_role != 'super-admin':
				delete_user = delete_document('admins',op_admin_id)
				if delete_user:
					del app.config['ADMINS'][op_admin_id]
					return jsonify({'msg': 'User deleted successfully'}), 200
				else:return jsonify({'msg': "couldn't delete user"}), 400
			else:return jsonify({'msg': 'Unauthorized'}), 403

		elif action == 'edit-signup-configs':
			passkey = request.form.get('passkey')
			s_link = request.form.get('secret_link')
			admin = session.get('ADMIN')

			if admin['role'] == 'super-admin':
				app.config['ENV_VALUES']['ADMIN_SECRET'] = passkey
				app.config['ENV_VALUES']['SIGNUP_LINK'] = s_link

				for key, value in app.config['ENV_VALUES'].items():
					set_key(env_path, key, value)
				app.config['PASS_KEY'] = passkey
				app.config['S_LINK'] = s_link

				return jsonify({'msg': 'Configs updated successfully'}), 200

			return jsonify({'msg': 'Unauthorized'}), 403

	except Exception as error:
		print(error)
		return jsonify({'msg': 'admin update unsccuessful'}), 500


@app.route('/platforms',methods=['GET'])
@login_required
@blocked
def index():
	g.page = 'platforms'
	platform_id = request.args.get('platform')
	action = request.args.get('action')

	if not platform_id and not action:
		try:
			platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
			query = platforms_ref.order_by('added_at', direction='DESCENDING').get()
			platforms = []

			for platform_doc in query:
				platform = platform_doc.to_dict()
				platform['id'] = platform.get('id')
				platform['added_at'] = platform.get('added_at').strftime("%Y-%m-%d %H:%M:%S"),
				platform['added_at'] = platform['added_at'][0]
				platform['name'] = str(platform.get('name')).upper()
				platform['admin'] = platform.get('admin')
				platforms.append(platform)
				session['PLATFORMS'][platform['id']] = platform

			return render_template("index.html", platforms=platforms)
		except Exception as error:
			print(error)
			return abort(500)
	
	elif action == 'add-platform':
		g.page = 'add-platform'
		return render_template("index.html", action=action)
	
	elif action == 'delete-platform':
		platform_ids = list(session['PLATFORMS'].keys())
		if platform_id in platform_ids:
			try:
				platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
				platforms_ref.document(platform_id).delete()
				del session['PLATFORMS'][platform_id]
				if session.get('PLATFORM') and platform_id == session.get('PLATFORM')['id']:
					del session['PLATFORM']
				return redirect('/dashboard')
			except Exception as error:
				print(error)
				return abort(500)
	
	else:
		session['PLATFORM'] = session['PLATFORMS'].get(platform_id)
		current_url = session.get('CURRENT_URL')
		url = str(current_url) if current_url is not None else '/accounts'
		return redirect(url)

@app.route('/add-platform', methods=['POST'])
@login_required
@blocked
def add_platform():
	try:
		platform_name = request.form.get('platform-name')
		platforms = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms').get()

		if len(platforms) > 0:
			platforms = [platform.to_dict()['name'].lower() for platform in platforms]
			if str(platform_name).lower() in platforms:
				return jsonify({'msg':'platform already exists'}), 400
		
		if str(platform_name).capitalize() in app.config['PLATFORMS']:
			platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
			platform_id = str(uuid.uuid4())
			platform_data = {
				'id': platform_id,
				'name': platform_name,
				'added_at':firestore.SERVER_TIMESTAMP
			}
			platforms_ref.document(platform_id).set(platform_data)

			return jsonify({'msg': 'platform added successfully'}), 200
		return jsonify({'msg': 'not authorized'}), 403
	except Exception as error:
		print(error)
		return jsonify({'msg': 'error adding platform'}), 500

@app.route('/models', methods = ['GET'])
@login_required
@blocked
@check_platform
def models():
	g.page = 'models'
	model_id = request.args.get('model')
	platform_id = session['PLATFORM']['id']
	action = request.args.get('action')

	platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
	models_ref = platforms_ref.document(platform_id).collection('models')

	if not model_id and not action:
		models = models_ref.order_by('added_at', direction='DESCENDING').get()

		models_list = [{
			'id': model.id,
			'full_name': str(model.get('full_name')),
			'added_at':model.get('added_at').strftime("%Y-%m-%d %H:%M:%S"),
			'socials': json.loads(model.get('socials'))
		} for model in models]

		for model in models_list:
			session['MODELS'].update({model['id']: model})

		return render_template('models.html', models=models_list)
	
	elif action == 'add-model':
		g.page = 'add-model'
		return render_template('models.html', action=action)
	
	else:
		model_ids = [u['id'] for u in list(session['MODELS'].values())]

		if model_id in model_ids:
			if action == 'set-model':
				schedules_ref = models_ref.document(model_id).collection('schedules')
				model_swipe_schedules = schedules_ref.where(field_path='type',op_string='==',value='swiping').get()
				model_swipe_schedules = [{'id':s.to_dict()['id'],'name':s.to_dict()['name']} for s in model_swipe_schedules]

				configs_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('configs')
				configs_snap = configs_ref.get()
				model_configs = {}
				for config in configs_snap:
					model_configs.update({config.to_dict()['title']:config.to_dict()})
				
				
				session['MODEL'] = session['MODELS'][model_id]
				session['MODEL']['CONFIGS'] = model_configs
				session['MODEL']['SCHEDULE'] = {}
				g.model = session['MODEL']
				current_url = session.get('CURRENT_URL')
				url = str(current_url) if current_url is not None else '/models'
				return redirect(url)
			
			elif action == 'edit-model':
				model = session['MODELS'][model_id]
				images_ref = models_ref.document(model_id).collection('images')
				accounts_ref = models_ref.document(model_id).collection('accounts')
				tasks_ref = models_ref.document(model_id).collection('tasks')

				model_images = len(images_ref.get())
				model_accounts = len(accounts_ref.get())
				model_tasks = len(tasks_ref.get())

				return render_template('models.html', model=model, action=action,
									   model_images=model_images, model_accounts=model_accounts, model_tasks=model_tasks)
		
			elif action == 'delete-model':
				model_ref = platforms_ref.document(platform_id).collection('models').document(model_id)
				model_data = model_ref.get().to_dict()
				model_ref.delete()

				del session['MODELS'][model_id]

				if session.get('MODEL') and model_id == session.get('MODEL')['id']:
					del session['MODEL']

				return redirect('/models')

		return redirect('/models')
		
@app.route('/models/<action>', methods=['POST']) #modified
@login_required
@blocked
@check_platform
def model(action):
	try:
		platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
		platform_id = session['PLATFORM']['id']
		models_ref = platforms_ref.document(platform_id).collection('models')
		panel_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]
		

		if action == 'add-model':
			full_name = request.form.get('model-fullname')
			username = request.form.get('model-uname')
			swipe_percent = request.form.get('model-swipe-percent')
			social_platforms = request.form.getlist('platform')
			social_handles = request.form.getlist('handles')

			model_socials = []
			if check_values([social_platforms,social_handles]):
				model_socials = [{"platform": platform, "handles": handle.split('\n')} 
					for platform,handle in zip(social_platforms, social_handles)]


			model_id = str(uuid.uuid4())

			models_ref.document(model_id).set({
				'id': model_id,
				'full_name': full_name,
				'socials': json.dumps(model_socials),
				'added_at':firestore.SERVER_TIMESTAMP
			})

			model_configs = panel_creds['configs']
			
			for config in model_configs:
				models_ref.document(model_id).collection('configs').document(config['title']).set(config)

			model = models_ref.document(model_id).get().to_dict()
			model_socials = json.loads(model.get('socials'))
			session['MODELS'].update({model_id: {
				'id': model.get('model_id'),
				'full_name':model.get('full_name'),
				'added_at': model.get('added_at').strftime("%Y-%m-%d %H:%M:%S"),
				'socials': model_socials
			}})

			return jsonify({'msg': 'model added successfully'}), 200
		
		elif action == 'edit-model':
			full_name = request.form.get('model-fullname')
			username = request.form.get('model-uname')
			swipe_percent = request.form.get('model-swipe-percent')
			model_id = request.form.get('model-id')
			model_socials = request.form.get('model-socials')
			socials = model_socials.split(',')
			model_socials = [
			    {
			        "platform": social.split(':')[0],
			        "handle": social.split(':')[1]
			    } for social in socials if social.strip()]
			
			model_ref =platforms_ref.document(platform_id).collection('models').document(model_id)
			model_ref.update({
				'full_name': full_name,
				'socials': json.dumps(model_socials)
			})

			schedules_ref = models_ref.document(model_id).collection('schedules')
			model_swipe_schedules = schedules_ref.where(field_path='type',op_string='==',value='swiping').get()
			model_swipe_schedules = [{'id':s.to_dict()['id'],'name':s.to_dict()['name']} for s in model_swipe_schedules]
			
			
			configs_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('configs')
			configs_snap = configs_ref.get()
			model_configs = []
			for config in configs_snap:
				model_configs.append(config.to_dict())
			
			model = model_ref.get().to_dict()
			model_socials = json.loads(model.get('socials'))
			session['MODEL'] = {
				'id': model.get('model_id'),
				'full_name':model.get('full_name'),
				'added_at': model.get('added_at').strftime("%Y-%m-%d %H:%M:%S"),
				'socials': model_socials
			}

			session['MODEL']['CONFIGS'] = model_configs
			g.model = session['MODEL']

			return jsonify({'msg': 'model updated successfully'}), 200
		
		elif action == 'set-model':
			model_id = request.get_json()['data']
			model_ids = [u['id'] for u in list(session['MODELS'].values())]
			if model_id in model_ids:
				if action == 'set-model':
					schedules_ref = models_ref.document(model_id).collection('schedules')
					model_swipe_schedules = schedules_ref.where(field_path='type',op_string='==',value='swiping').get()
					model_swipe_schedules = [{'id':s.to_dict()['id'],'name':s.to_dict()['name']} for s in model_swipe_schedules]

					configs_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('configs')
					configs_snap = configs_ref.get()
					model_configs = {}
					for config in configs_snap:
						model_configs.update({config.to_dict()['title']:config.to_dict()})
					
					
					session['MODEL'] = session['MODELS'][model_id]
					session['MODEL']['CONFIGS'] = model_configs
					session['MODEL']['SCHEDULE'] = {}
					g.model = session['MODEL']
					return jsonify({'msg': 'model set successfully', 'model': session['MODEL'],'model_swipe_schedules':model_swipe_schedules}), 200
	
	except Exception as error:
		print(error)
		return jsonify({'msg': 'error updating model'}), 500

@app.route('/signup',methods=['POST','GET'])
@login_required
@check_super
def signup():
	if request.method == 'GET':
		if session['ADMIN']['role'] == 'super-admin':
			return render_template('signup.html')
		else:return redirect(url_for('index'))
	elif request.method == 'POST':
		if session['ADMIN']['role'] == 'super-admin':
			full_name = request.form.get('full-name')
			email = request.form.get('email')
			password = request.form.get('password')
			passkey = request.form.get('passkey')

			uid = str(uuid.uuid4())
			role = 'admin'
			status = 'active'
			
			if not full_name or not email or not password:
				return jsonify({'msg': 'Some entries are empty, fill all fields'}), 400
			elif not validate_email(email):
				return jsonify({'msg': 'Not a valid email'}), 400
			elif len(str(password)) < 8:
				return jsonify({'msg': 'Password must be 8 or more characters'}), 400
			elif not validate_password(password):
				return jsonify({'msg': 'Password must contain 8 or more characters of letters and digits'}), 400

			# Hash the password
			password_hash = generate_password_hash(password)

			# Check if email already exists
			admins_collection = app.config['ADMINS_REF']
			email_exists = admins_collection.where(field_path='email', op_string='==', value=email).limit(1).get()

			if email_exists:
				return jsonify({'msg': 'Email already exists'}), 400

			# Create the admin document in Firestore
			admin_doc_ref = admins_collection.document(uid)
			admin_doc_ref.set({
				'id': uid,
				'full_name': full_name,
				'email': email,
				'password': password_hash,
				'role': role,
				'status': status,
				'created_at': firestore.SERVER_TIMESTAMP
			})
			
			return jsonify({'msg': 'Signup successful'}), 200
	return jsonify({'msg':'Not authorized'}),403

@app.route(f'/signup/<key>', methods=['GET'])
def signup_page(key):
	g.page = 'signup-hidden'
	if key and key == app.config['S_LINK']:
		if 'ADMIN' not in session:return render_template('signup.html')
		else:return redirect(url_for('index'))
	return abort(404)

@app.route(f'/adminonlyallowedtosignup__________',methods=['POST'])
def do_signup():
	try:
		if request.method == 'GET':
			return redirect(url_for('login'))

		full_name = request.form.get('full-name')
		email = request.form.get('email')
		password = request.form.get('password')
		passkey = request.form.get('passkey')

		uid = str(uuid.uuid4())
		role = 'admin'
		status = 'active'

		if not validate_passkey(passkey):
			return jsonify({'msg': "You're not allowed"}), 403
		elif not full_name or not email or not password:
			return jsonify({'msg': 'Some entries are empty, fill all fields'}), 400
		elif not validate_email(email):
			return jsonify({'msg': 'Not a valid email'}), 400
		elif len(str(password)) < 8:
			return jsonify({'msg': 'Password must be 8 or more characters'}), 400
		elif not validate_password(password):
			return jsonify({'msg': 'Password must contain 8 or more characters of letters and digits'}), 400

		# Hash the password
		password_hash = generate_password_hash(password)

		# Check if email already exists
		admins_collection = app.config['ADMINS_REF']
		email_exists = admins_collection.where(field_path='email', op_string='==', value=email).limit(1).get()

		if email_exists:
			return jsonify({'msg': 'Email already exists'}), 400

		# Create the admin document in Firestore
		admin_doc_ref = admins_collection.document(uid)
		admin_doc_ref.set({
			'id': uid,
			'full_name': full_name,
			'email': email,
			'password': password_hash,
			'role': role,
			'status': status,
			'created_at': firestore.SERVER_TIMESTAMP
		})

		# Retrieve the created admin document from Firestore
		admin_doc = admin_doc_ref.get().to_dict()

		admin = {
			'id': admin_doc['id'],
			'full_name': admin_doc['full_name'],
			'email': admin_doc['email'],
			'password': admin_doc['password'],
			'role': admin_doc['role'],
			'status': admin_doc['status'],
			'created_at': admin_doc['created_at']
		}

		# Add the admin to the app's configuration
		app.config['ADMINS'].update({admin['id']: admin})

		return jsonify({'msg': 'Signup successful'}), 200

	except Exception as error:
		print(error)
		return abort(500)
	
@app.route('/login', methods=['GET', 'POST'])
def login():
	try:
		if request.method == 'GET':
			if 'ADMIN' not in session:
				return render_template('login.html')
			else:
				return redirect(url_for('index'))
		elif request.method == 'POST':
			email = request.form.get('email')
			password = request.form.get('password')

			if not email or not password:
				return jsonify({'msg': 'some entries are empty, fill all fields'}), 400

			admins_ref = app.config['ADMINS_REF']
			admin_query = admins_ref.where(field_path='email', op_string='==', value=email).limit(1).get()
			if not admin_query:
				return jsonify({'msg': 'user does not exist'}), 403

			admin_doc = admin_query[0]
			admin = admin_doc.to_dict()
			hashed_password = admin['password']

			if admin['status'] != 'active':
				return jsonify({'msg': 'account blocked'}), 403

			if not check_password_hash(hashed_password, password):
				return jsonify({'msg': 'wrong password'}), 403

			session['ADMIN'] = admin
			session['PLATFORMS'] = {}
			session['MODELS'] = {} 
			

			return jsonify({'msg': 'login successful'}), 200
				
	except Exception as error:
		print(error)
		abort(500)

@app.route('/logout',methods=['GET','POST'])
@login_required
def do_logout():
	try:
		if request.method == 'GET':
			if logout(): 
				response = make_response(jsonify({'msg': f"Logout successful"}), 200)
				response.delete_cookie('session')
				return response
			return jsonify({'msg':'logout unsuccessful'}), 400
		elif request.method == 'POST':
			if logout(): 
				response = make_response(jsonify({'msg': f"Logout successful"}), 200)
				response.delete_cookie('session')
				return response
			return jsonify({'msg':'logout unsuccessful'}), 400
	except Exception as error:
		print(error)
		return jsonify({'msg':'logout unsuccessful'}), 500

@app.route('/schedules',methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def schedules():
	g.page = 'schedules'
	action = request.args.get('action')
	action_type = request.args.get('type')
	s_id = request.args.get('s')
	next = request.args.get('next')
	interval = request.args.get('interval',0)
	interval = int(interval)
	swipe_percent = request.args.get('swipe_percent')

	platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
	platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
	schedules_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('schedules')

	account_schedules= schedules_ref.where(field_path='type',op_string='==',value='account').order_by('added_at', direction='DESCENDING').get()
	swipe_schedules= schedules_ref.where(field_path='type',op_string='==',value='swiping').order_by('added_at', direction='DESCENDING').get()
	
	account_schedules = [s.to_dict() for s in account_schedules]
	swipe_schedules = [s.to_dict() for s in swipe_schedules]

	if not action and not s_id:
		schedules = schedules_ref.order_by('added_at', direction='DESCENDING').get()
		schedules = [s.to_dict() for s in schedules]
		if len(schedules) > 0:
			return render_template('schedules.html', schedules=schedules)

		return render_template('schedules.html', action='add-schedule', action_type='account',
							   models=list(session['MODELS'].values()), swipe_schedules=swipe_schedules,
							   schedules=account_schedules, next=next)

	elif action == 'edit-schedule' and s_id:
		schedule = schedules_ref.document(s_id).get()
		if schedule.exists:
			schedule = schedule.to_dict()
			schedule['daily_percent'] = json.loads(schedule['daily_percent'])
			schedule['day_specs'] = json.loads(schedule['day_specs'])
			session['MODEL']['SCHEDULE'] = schedule
			return render_template('schedules.html', action='edit-schedule',
								schedule=schedule, swipe_schedules=swipe_schedules,
								models=list(session['MODELS'].values()), action_type=action_type, next=next)
		
		else:
			return redirect(url_for('schedules'))

	elif action == 'next':
		if action_type == 'edit':
			day_specs = session['MODEL']['SCHEDULE']['day_specs']
			return render_template('schedules.html', action=action, s_id=s_id, action_type=action_type,
								   day_specs=day_specs, next=next,interval=interval)

		return render_template('schedules.html', action=action, s_id=s_id, next=next,interval=interval,swipe_percent=swipe_percent)

	return render_template('schedules.html', action=action, action_type=action_type,
						   models=list(session['MODELS'].values()), swipe_schedules=swipe_schedules, next=next)

@app.route('/schedules/<action>', methods=['POST'])
@login_required
@blocked
@check_platform
@check_model
def scheduler(action):
	try:
		platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
		platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
		schedules_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('schedules')

		if action == 'add-schedule':
			name = request.form.get('s-name')
			type = request.form.get('s-type')
			swipe_percent = request.form.get('s-swipe-percent')
			s_session_count_start = request.form.get('s-session-count-start')
			s_session_count_end = request.form.get('s-session-count-end')
			s_delay_start = request.form.get('s-swipe-delay-start')
			s_delay_end = request.form.get('s-swipe-delay-end')
			s_duration_start = request.form.get('s-duration-start')
			s_duration_end = request.form.get('s-duration-end')
			s_start = request.form.get('s-start')
			s_end = request.form.get('s-end')

			s_start = s_start + ':00' if len(s_start.split('T')[1].split(':')) == 2 else s_start
			s_end = s_end + ':00' if len(s_end.split('T')[1].split(':')) == 2 else s_end

			s_session_count = f'{s_session_count_start}-{s_session_count_end}'
			s_delay = f'{s_delay_start}-{s_delay_end}'
			s_duration = f'{s_duration_start}-{s_duration_end}'

			op_count = request.form.get('op-count')
			max_workers = request.form.get('max-workers')

			op_sleep_timer_count = request.form.get('s-tf-acc-count')
			op_sleep_timer_time = request.form.get('s-tf-acc-time')
			timer = {"count_": op_sleep_timer_count, "time": op_sleep_timer_time} if op_sleep_timer_count else {"count_": 0, "time": 0}

			op_proxies = request.form.get('op-proxies')
			op_location = request.form.get('op-location')
			op_swipe_group = request.form.get('op-swipe-group')
			next = request.form.get('next')

			model = session['MODEL']['id']
			platform = session['PLATFORM']['id']

			s_id = str(uuid.uuid4())
			schedule_ref = schedules_ref.document(s_id)


			if type.lower() in ['swiping', 'swipe']:
				d1 = datetime.strptime(s_start, '%Y-%m-%dT%H:%M:%S')
				d2= datetime.strptime(s_end, '%Y-%m-%dT%H:%M:%S')
				date_interval = d2 - d1
				date_interval = date_interval.days
				session['MODEL']['SCHEDULE'] = {
					'id': s_id,
					'model': model,
					'platform': platform,
					'name': name,
					'type': type.lower(),
					'swipe_percent': swipe_percent,
					'op_start_at': s_start,
					'op_end_at': s_end,
					'swipe_session_count': s_session_count,
					'swipe_delay': s_delay,
					'swipe_duration': s_duration,
					'running':False
				}

				if date_interval <= 1:
					schedule_ref = schedules_ref.document(s_id)
					schedule = session['MODEL']['SCHEDULE']
					schedule['added_at'] = firestore.SERVER_TIMESTAMP
					schedule['current_day'] = 0
					schedule['day_specs'] = json.dumps([])
					schedule['daily_percent'] = json.dumps([{'day':1,'swipe_percent':swipe_percent}])
					schedule_ref.set(schedule)
					return jsonify({'msg': 'schedule added successfully', 'next': '/schedules'}), 200
				
				return jsonify({'msg': 'schedule added, add date specs', 'schedule': s_id, 'action': 'finish-schedule', 'action_type': 'add', 'next': next,'date_interval':date_interval,'swipe_percent':swipe_percent}), 200

			elif type.lower() == 'account':
				session['MODEL']['SCHEDULE'] = {
					'id': s_id,
					'model': model,
					'platform': platform,
					'name': name,
					'type': type.lower(),
					'op_count': op_count,
					'op_timer': json.dumps(timer),
					'op_swipe_group': op_swipe_group,
					'op_proxies': op_proxies,
					'op_location': op_location,
					'op_max_workers': max_workers,
					'op_start_at': s_start,
					'op_end_at': s_end,
					'running':False
				}
			return jsonify({'msg': 'schedule added successfully', 'next': next}), 200

		elif action == 'edit-schedule':
			type = request.form.get('s-type')
			name = request.form.get('s-name')
			swipe_percent = request.form.get('s-swipe-percent')
			s_session_count = request.form.get('s-session-count')
			s_delay = request.form.get('s-swipe-delay')
			s_duration = request.form.get('s-duration')
			s_start = request.form.get('s-start')
			s_end = request.form.get('s-end')
			s_id = request.form.get('s-id')

			s_start = s_start + ':00' if len(s_start.split('T')[1].split(':')) == 2 else s_start
			s_end = s_end + ':00' if len(s_end.split('T')[1].split(':')) == 2 else s_end
			
			op_count = request.form.get('op-count')
			max_workers = request.form.get('max-workers')

			op_sleep_timer_count = request.form.get('s-tf-acc-count')
			op_sleep_timer_time = request.form.get('s-tf-acc-time')
			timer = {"count_": op_sleep_timer_count, "time": op_sleep_timer_time} if op_sleep_timer_count else {"count_": "0", "time": "0"}

			op_proxies = request.form.get('op-proxies')
			op_location = request.form.get('op-location')

			op_swipe_group = request.form.get('op-swipe-group')
			next = request.form.get('next')
			
			model = session['MODEL']['id']
			platform = session['PLATFORM']['id']

			d1 = datetime.strptime(s_start, '%Y-%m-%dT%H:%M:%S')
			d2= datetime.strptime(s_end, '%Y-%m-%dT%H:%M:%S')
			date_interval = d2 - d1
			date_interval = date_interval.days
			
			schedule_ref = schedules_ref.document(s_id).get()

			# if schedule_ref.to_dict()['running']:
			# 	return jsonify({'msg': 'cannot edit a running schedule'}), 400
			
			if type.lower() in ['swiping', 'swipe']:
				day_specs = json.loads(schedule_ref.to_dict().get('day_specs'))
				session['MODEL']['SCHEDULE'] = {
					'id':s_id,
					'model': model,
					'name': name,
					'swipe_percent': swipe_percent,
					'op_start_at': s_start,
					'op_end_at': s_end,
					'swipe_session_count': s_session_count,
					'swipe_delay': s_delay,
					'swipe_duration': s_duration,
					'day_specs':day_specs
				}

				if date_interval <= 1:
					schedule_ref = schedules_ref.document(s_id)
					schedule = session['MODEL']['SCHEDULE']
					schedule['day_specs'] = json.dumps(day_specs)
					schedule['daily_percent'] = json.dumps([{'day':1,'swipe_percent':swipe_percent}])
					schedule_ref.update(schedule)
				return jsonify({'msg': 'schedule updated successfully, add date specs', 'schedule': s_id, 'action': 'finish-schedule', 'action_type': 'edit', 'next': next,'date_interval':date_interval}), 200

			elif type.lower() == 'account':
				session['MODEL']['SCHEDULE'] = {
					'model': model,
					'name': name,
					'op_count': op_count,
					'op_timer': json.dumps(timer),
					'op_swipe_group': op_swipe_group,
					'op_proxies': op_proxies,
					'op_location': op_location,
					'op_max_workers': max_workers,
					'op_start_at': s_start,
					'op_end_at': s_end
				}
			return jsonify({'msg': 'schedule updated successfully', 'next': next}), 200

		elif action == 'finish-schedule':
			s_id = request.form.get('s-id')
			days = request.form.getlist('s-day')
			percents = request.form.getlist('s-swipe-percent')
			interval = request.form.get('interval',0)
			interval = int(interval)


			day_specs = [{"day": day, "swipe_percent": percent} for day, percent in zip(days, percents)]
			daily_percent = share_daily_percent(day_specs)

			if len(daily_percent) < interval:return jsonify({'msg':'swipe percentage not properly shared amongst days'}),400

			action_type = request.form.get('action-type')
			next = request.form.get('next')

			if len(daily_percent) < interval:
				return jsonify({'msg': 'number of days sepcified cannot be less than the date interval', 'next': next}), 400
			
			if session['MODEL']['SCHEDULE']['id'] == s_id:
				schedule_ref = schedules_ref.document(s_id)
				schedule = session['MODEL']['SCHEDULE']
				schedule['day_specs'] = json.dumps(day_specs)
				schedule['daily_percent'] = json.dumps(daily_percent)

				if action_type and action_type == 'edit':
					schedule_ref.update(schedule)
					return jsonify({'msg': 'schedule updated successfully', 'next': next}), 200
				
				schedule['added_at'] = firestore.SERVER_TIMESTAMP
				schedule['current_day'] = 0
				schedule_ref.set(schedule)

				return jsonify({'msg': 'schedule added successfully', 'next': next}), 200

			return jsonify({'msg':'schedule not in session'}), 404

		elif action == 'delete-schedule':
			s_id = request.get_json()['data'][0]['id']
			schedule_ref = schedules_ref.document(s_id).get()
			if schedule_ref.to_dict()['running']:
				return jsonify({'msg': 'cannot edit a running schedule'}), 400
			
			schedules_ref.document(s_id).delete()

			session['MODEL']['SCHEDULE'].clear()
			return jsonify({'msg': 'schedule deleted successfully'}), 200
		
	except Exception as error:
		print(error)
		return jsonify({'msg':f"couldn't {action.replace('-',' ')}"}), 400

@app.route('/accounts',methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def accounts():
	g.page = 'accounts'
	accounts = []
	action = request.args.get('action')

	if action and action == 'load-accounts':
		return render_template("accounts.html",action=action)

	platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
	platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
	accounts_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('accounts')

	query = accounts_ref.get()
	total = len(query)

	page = int(request.args.get('page', 1))
	limit = int(request.args.get('limit', 20))
	offset = (page - 1) * limit if page <= total else 0

	# Retrieve the accounts with pagination
	query = accounts_ref.order_by('created_at', direction='DESCENDING')
	query = query.limit(limit).offset(offset)
	accounts = query.get()

	# Prepare the accounts data
	accounts = [account.to_dict() for account in accounts]
	sum = min(offset + len(accounts), total)

	return render_template("accounts.html", accounts=accounts, sum=sum, total=total, page=page, limit=limit)

@app.route('/account-page',methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def account_page():
	g.page = 'account-page'
	account_id = request.args.get('account')
	action = request.args.get('action')
	images = []
	matches = {}
	if account_id:
		platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
		platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
		accounts_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('accounts')
		
		panel_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]
		panel_edit_configs = panel_creds['edit_configs']

		account_snap = accounts_ref.document(account_id).get()
		if account_snap.exists:
			account_data = account_snap.to_dict()
			account_data['profile'] = json.loads(account_data['profile']) if isinstance(account_data['profile'],str) else account_data['profile']
			account_data['profile_image'] = account_data.get('images')[0] if 'images' in account_data.keys() else ''
			
			last_updated = account_data.get('last_updated')
			if last_updated is not None:
				last_updated = datetime.strptime(last_updated.split(".")[0], '%Y-%m-%d %H:%M:%S')
				time_difference = datetime.now() - last_updated
				account_data['time_ago'] = round(time_difference.total_seconds() / 3600)
			else:
				account_data['time_ago'] = 0
			
			if action and action == 'map':
				return render_template('account-page.html', account=account_data, action=action)
			elif action and action == 'edit-account':
				edit_data = panel_edit_configs
				return render_template('account-page.html', account=account_data, action=action,edit_data=edit_data)
			elif action and action == 'view-details':
				return render_template('account-page.html', account=account_data, action=action)
			return render_template('account-page.html', account=account_data)
	return redirect(url_for('accounts'))

@app.route('/account-page/<action>',methods=['POST'])
@login_required
@blocked
@check_platform
@check_model
def account_action(action):
	try:
		platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
		platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
		accounts_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('accounts')
		configs_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('configs')
		panel_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]
		
		panel_edit_configs = panel_creds['edit_configs']
		panel_email = panel_creds['email']
		panel_pass = panel_creds['password']
		panel_key = panel_creds['key']
		panel_edit_configs = panel_creds['edit_configs']

		TOKEN = api.get_token(panel_email, panel_pass, panel_key)
		if not TOKEN[0]:
			return jsonify({'msg': TOKEN[1]}), 403
		TOKEN = TOKEN[1]['idToken']

		if action == 'edit-account':
			form_data = request.form
			account_id = form_data.get('account-id')

			account_profile = {
				'bio':form_data.get('bio'),
				'height':form_data.get('height')
			}
			for key in panel_edit_configs.keys():
				account_profile[key] = form_data.getlist(key) if key.lower() in ['languages'] else form_data.get(key)

			update_profile = api.update_profile(panel_creds['url'],account_id,TOKEN,json_data=account_profile)
			if  update_profile[0]:
				if  update_profile[1].status_code == 200:
					account_data = accounts_ref.document(account_id).get()
					if account_data.exists:
						account_data = account_data.to_dict()
						for key,value in update_profile[1].json()['success'].items():
							if value:account_data['profile'][key] = account_profile[key]
						accounts_ref.document(account_id).update(account_data)
						return jsonify({'msg': 'account updated successfully'}), 200
					else:raise ValueError('account does not exist')
				elif update_profile[1].status_code <= 400:
					return jsonify({'msg':update_profile[1].json()['message']})
			return jsonify({'msg': f'account update unsuccessful'}), 400
		
		elif action == 'map':
			account_id = request.get_json()['account_id']
			location = request.get_json()['data']

			update_location = api.update_location(panel_creds['url'],account_id,TOKEN,json_data=location)
			if update_location[0]:
				update_location = update_location[1]
				if update_location.status_code == 200:
					account_data = accounts_ref.document(account_id).get()
					if account_data.exists:
						accounts_ref.document(account_id).update({'city':update_location.json()['location']})
						return jsonify({'msg': 'location updated successfully'}), 200
					else:raise ValueError('account does not exist')
				elif update_location.status_code <= 400: 
					return jsonify({'msg':update_location.json()['message']}), update_location.status_code
			return jsonify({'msg': f'location update unsuccessful'}), 400
		
		elif action == 'update-account':
			account_id = request.get_json()['data'][0]['id']

			proxies  = configs_ref.document('Proxies').get().to_dict()
			json_data = {'proxies':proxies['content']} if check_values([proxies['content']]) else {}
			account_stats = api.get_stats(panel_creds['url'],account_id,TOKEN,json_data=json_data)
			account_snapshot = api.get_profile(panel_creds['url'],account_id,TOKEN)
			
			if account_snapshot[0] and account_stats[0]:
				account_data = account_snapshot[1]
				account_stats = account_stats[1]

				if account_data.status_code > 200 and account_data.status_code <= 400:
					return jsonify('msg',account_data.json()['message']), account_data.status_code
				
				elif account_stats.status_code > 200 and account_stats.status_code <= 400:
					return jsonify('msg',account_stats.json()['message']), account_stats.status_code

				account_data = account_data.json()
				account_stats = account_stats.json()
				account_data['last_updated'] = str(datetime.now())
				account_data['stats'] = account_stats['stats']
				account_data['stats']['swipes'] = 0
				account_data['stats']['liked'] = 0
				account_data['stats']['disliked'] = 0

				account_data['status'] = account_stats['status']
				for stat in account_data['stats']:
					if stat < 0:account_data['status'] = 'BANNED'
				accounts_ref.document(account_id).update(account_data)

				return jsonify({'msg':'details updated successfully'}), 200
			
			return jsonify({'msg': f'account update unsuccessful.'}), 400
		
		elif action == 'delete-account':
			account_id = request.get_json()['data'][0]['id']
			account_snapshot = api.delete_account(panel_creds['url'],account_id,TOKEN)
			
			if account_snapshot[0]:
				account_snap = account_snapshot[1]
				if account_snap.status_code == 200:
					accounts_ref.document(account_id).delete()
					return jsonify({'msg':'account deleted successfully'}), 200
				elif account_snap.status_code <= 400:
					return jsonify({'msg':account_snap.json()['message']}), account_snap.status_code
			return jsonify({'msg': f'account delete unsuccessful'}),400
			
	except ValueError as error:
		return jsonify({'msg': f'account {action.split("-")[0]} unsuccessful. {error}'}), 400
	
	except Exception as error:
		print(error)
		return jsonify({'msg': f'account {action.split("-")[0]} unsuccessful'}), 500
	
@app.route('/create-accounts',methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def show_create_accounts():
	g.page = 'create-accounts'
	action = request.args.get('action')
	platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
	platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms').document(platform_id)
	models_ref = platforms_ref.collection('models').document(model_id)
	accounts_ref = models_ref.collection('accounts')
	schedules_ref = models_ref.collection('schedules')
	tasks_ref = models_ref.collection('tasks')

	task_status = session['MODEL'].get('TASKS')
	if check_values([task_status]):
		task_doc = tasks_ref.document(task_status['account_task']['id']).get()
		if task_doc.exists:
			task_data = task_doc.to_dict()
			task_status = {
				'id':task_data['id'],
				'type': task_data['type'],
				'start_time': task_data['start_time'],
				'status': task_data['status'],
				'running':task_data['running'],
				'progress':task_data['progress']
			}
			session['MODEL']['TASKS']['account_task']['id'] = task_data['id']
			session['MODEL']['TASKS']['account_task']['status'] =task_data['status']
			session['MODEL']['TASKS']['account_task']['running'] =task_data['running']
			session['MODEL']['TASKS']['account_task']['progress'] =task_data['progress']
		else:task_status = {'status':'','running':False,'id':str(uuid.uuid4())}
	else:task_status = {'status':'','running':False,'id':str(uuid.uuid4())}
	
	if action and action == 'upload-accounts':
		return render_template('create-accounts.html',running=task_status['running'],task_status=task_status,action=action)

	account_schedules= schedules_ref.where(field_path='type',op_string='==',value='account').order_by('added_at', direction='DESCENDING').get()
	swipe_schedules= schedules_ref.where(field_path='type',op_string='==',value='swiping').order_by('added_at', direction='DESCENDING').get()
	
	account_schedules = [s.to_dict() for s in account_schedules]
	swipe_schedules = [s.to_dict() for s in swipe_schedules]
	
	models = [s for s in list(session['MODELS'].values())]
	genders = app.config['GENDERS']
	return render_template('create-accounts.html',
						   schedules=account_schedules,
						   swipe_schedules=swipe_schedules,
						   running=task_status['running'],
						   task_status=task_status,
						   model=session['MODEL'],
						   models=models,
						   genders = genders)
	
@app.route('/create-accounts',methods=['POST'])
@login_required
@blocked
@check_platform
@check_model
def create_accounts():
	try:
		platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
		platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms').document(platform_id)
		models_ref = platforms_ref.collection('models').document(model_id)
		accounts_ref = models_ref.collection('accounts')
		images_ref = models_ref.collection('images')
		tasks_ref = models_ref.collection('tasks')
		configs_ref = models_ref.collection('configs')
		schedules_ref = models_ref.collection('schedules')

		panel_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]
		panel_email = panel_creds['email']
		panel_pass = panel_creds['password']
		panel_key = panel_creds['key']
		platform_host = panel_creds['url']
		panel_worker_key = panel_creds['worker_key']
		poses = panel_creds['poses']

		SERVER = app.config['SERVER']

		op_count = request.form.get('op-count',None)
		bio = request.form.get('bio',None)

		op_server_option = request.form.get('op-server-option')
		max_workers = request.form.get('max-workers',10)
		max_workers = int(max_workers) if max_workers != '' else 10

		if op_server_option == 'emulator':max_workers = 1

		profile_image_count = request.form.get('image-count',5)
		profile_image_count = int(profile_image_count)

		age_range_start = request.form.get('op-age-range-start')
		age_range_end = request.form.get('op-age-range-end')

		op_gender = request.form.get('op-gender')
		gender = op_gender if op_server_option == 'webapi' else 'female'
		gender_data = {
			'id': 'id_women' if gender == 'male' else 'id_men',
			'intersex_experience': 'no',
			'show_gender': True
		}
		
		if gender not in ['female','male']:
			op_gender_other= request.form.get('op-gender-other')
			op_gender_connections = request.form.get('op-gender-connections')
			op_gender_show = request.form.get('op-gender-show')
			op_gender_intersex = request.form.get('op-gender-intersex')
			gender = op_gender_other

			gender_data = {
				'id': 'id_women' if op_gender_connections == 'men' else 'id_men',
				'intersex_experience': op_gender_intersex,
				'show_gender': True if op_gender_show == 'yes' else False
			}

		if not check_values([op_count,age_range_start,age_range_end,gender]):raise ValueError(f'Empty values, fill in all inputs correctly')
		
		op_count = int(op_count)
		age_range = f'{age_range_start}-{age_range_end}'
		swipe_schedule = request.form.get('op-swipe-group',None)
		op_location = request.form.get('op-location',None)


		img_cursor = images_ref.get()
		images = [img.to_dict()['image'] for img in img_cursor if img.to_dict()['type'] == 'profile']
		
		if not check_values([images]):raise ValueError(f'No image for selected model')

		v_images = [{'pose':img.to_dict()['pose'],'link':img.to_dict()['image']} for img in img_cursor if img.to_dict()['type'] == 'verification']
		verification_images = {}
		for pose in poses:
			verification_images[pose] = [image['link'] for image in v_images if image['pose'] == pose]
			if not check_values([verification_images[pose]]):raise ValueError(f'No {pose} image for selected model')

		configs_snap = configs_ref.get()
		configs = {}
		for config in configs_snap:
			config = config.to_dict()
			if not check_values([config['content']]):
				raise ValueError(f'{config["title"]} is empty for selected model')
			
			config = {config['title']:config['content']}
			configs.update(config)

		names = configs['Names']
		bios = configs['Biographies']
		proxies = configs['Proxies'] 
		user_agents = configs['User Agents']
		cities = configs['Cities']

		creds = configs['Email and Password']
		if not check_values([creds]):
			raise ValueError(f'email:password is empty for selected model')
		
		handles = session['MODEL']['socials']
		handles = [h.replace('\r','') for handle in handles 
	     if handle['platform'].lower() in ['instagram','ig','insta'] 
		 for h in handle['handles']]
		

		if not check_values([swipe_schedule]):
			raise ValueError('no swipe schedule for the selected model')
		schedule = schedules_ref.document(swipe_schedule).get()
		if not schedule.exists:raise ValueError('No swiping schedule for selected model')
		swipe_configs = schedule.to_dict()

		start_date = swipe_configs['op_start_at']
		if datetime.fromisoformat(start_date) < datetime.now():
			return jsonify({'msg':'scheduled date is passed, please update!'}),400
		daily_percent = json.loads(swipe_configs['daily_percent'])
		swipe_configs['daily_percent'] = daily_percent

		swipe_delay_start = swipe_configs['swipe_delay'].split('-')[0]
		swipe_delay_end = swipe_configs['swipe_delay'].split('-')[1]
		swipe_configs['swipe_delay'] = random.randint(int(swipe_delay_start),int(swipe_delay_end))
		swipe_configs['min_wait'] = int(swipe_delay_start)
		swipe_configs['max_wait'] = int(swipe_delay_end)

		
		swipe_duration_start = swipe_configs['swipe_duration'].split('-')[0]
		swipe_duration_end = swipe_configs['swipe_duration'].split('-')[1]
		swipe_configs['swipe_duration'] = random.randint(int(swipe_duration_start),int(swipe_duration_end))

		swipe_session_count_start = swipe_configs['swipe_session_count'].split('-')[0]
		swipe_session_count_end= swipe_configs['swipe_session_count'].split('-')[1]
		swipe_configs['swipe_session_count'] = random.randint(int(swipe_session_count_start),int(swipe_session_count_end))

		swipe_configs['first_swipe'] = True
		TOKEN = api.get_token(panel_email, panel_pass, panel_key)
		if not TOKEN[0]:
			return jsonify({'msg': TOKEN[1]}), 403
		TOKEN = TOKEN[1]['idToken']

		used_emails = api.get_used_emails(panel_creds['url'],TOKEN)
		if used_emails[0]:
			used_emails = used_emails[1]
			if used_emails.status_code < 400:
				creds = [cred for cred in creds if cred not in used_emails.json()['accounts']]
			else:raise ValueError(f'{used_emails.json()["message"]}')
		else:raise Exception('error with getting used emails')
		if not check_values([creds]):raise ValueError('all emails already used')
		
		task_id = str(uuid.uuid4())
		task_status = 'running'
		task_progress = 0

		task_session = {
			'admin':session['ADMIN']['id'],
			'platform':platform_id,
			'model':model_id
		}

		kwargs = {
			'accounts_ref':accounts_ref,
			'tasks_ref':tasks_ref,
			'task_session':task_session,
			'swipe_configs':swipe_configs,
			'worker':panel_worker_key,
			'SERVER':SERVER,
			'server_option':op_server_option,
			'nb_of_accounts':op_count if op_server_option == 'emulator' else 1,
			'op_count': op_count,
			'nb_of_images':profile_image_count,
			'handles':[handles[:] for _ in range(op_count)],
			'bios': [bios[:] for _ in range(op_count)],
			'max_workers': max_workers,
			'task_id':task_id,
			'images': images,
			'verification_images':verification_images,
			'age_range':age_range,
			'gender':gender,
			'gender_data':gender_data,
			'names':[names[:] for _ in range(op_count)],
			'cities': [cities[:] for _ in range(op_count)],
			'proxies':[proxies[:] for _ in range(op_count)],
			'user_agents':[user_agents[:] for _ in range(op_count)],
			'accounts':[creds[:] for _ in range(op_count)],
			'url':platform_host,
			'token': TOKEN
		}

		if op_server_option == 'emulator':
			kwargs = {
				'server_option':op_server_option,
				'nb_of_accounts':op_count if op_server_option == 'emulator' else 1,
				'nb_of_images':profile_image_count,
				'handles':handles,
				'bios': bios,
				'task_session':task_session,
				'task_id':task_id,
				'profile_images': images,
				'verification_images':verification_images,
				'age_range':age_range,
				'gender':gender,
				'gender_data':gender_data,
				'names':names,
				'cities': cities,
				'proxies':proxies,
				'user_agents':user_agents,
				'accounts':creds,
				'url':platform_host,
				'token': TOKEN
			}

			task = TASKS().create_accounts(**kwargs)
			if task[0]:
				task = task[1]
				if task.status_code == 200:
					tasks_ref.document(task_id).set({
						'id':task_id,
						'type': 'Account Creation Operation',
						"start_time":firestore.SERVER_TIMESTAMP,
						'status': task_status,
						'progress': task_progress,
						'running':True,
						'failed':0,
						'successful':0,
						'task_count':op_count,
						'created_accounts':[],
						'swipe_config':swipe_configs,
						'message':'Account creation just started'
					})

					session['MODEL']['TASKS'] = {
						'account_task':{
							'id':task_id,
							'task_status':task_status,
							'running':True,
						}
					}
					return jsonify({'msg': 'Task started, please wait while it finishes'}), 200
				else:return jsonify({'msg':task.json()['message']}),task.status_code
			else:
				raise Exception(task[1])

		account_task = Thread(target=TASKS().start_account_creation, kwargs=kwargs)
		account_task.start()

		if account_task.is_alive():
			tasks_ref.document(task_id).set({
				'id':task_id,
				'type': 'Account Creation Operation',
				"start_time":firestore.SERVER_TIMESTAMP,
				'status': task_status,
				'progress': task_progress,
				'running':True,
				'failed':0,
				'successful':0,
				'task_count':op_count,
				'message':'Account creation just started'
			})

			session['MODEL']['TASKS'] = {
				'account_task':{
					'id':task_id,
					'task_status':task_status,
					'running':True,
				}
			}
			return jsonify({'msg': 'Task started, please wait while it finishes'}), 200
		else:
			return jsonify({'msg': 'No tasks running'}), 200
	except ValueError as v_error:
		print(v_error)
		return jsonify({'msg': f'{v_error}'}), 400
	except Exception as error:
		print(error)
		return jsonify({'msg': 'error starting task'}), 500

@app.route('/upload-accounts',methods=['POST'])
@login_required
@blocked
@check_platform
@check_model
def upload_accounts():
  try:
    platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
    platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
    accounts_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('accounts')
    tasks_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('tasks')
    configs_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('configs')

    configs_snap = configs_ref.get()
    configs = {}
    for config in configs_snap:
      config = config.to_dict()
      if config["title"]=='Proxies':
        configs['Proxies']=config['content']

    proxies = configs['Proxies'] 
    
    panel_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]
    panel_email = panel_creds['email']
    panel_pass = panel_creds['password']
    panel_key = panel_creds['key']
    platform_host = panel_creds['url']
    
    TOKEN = api.get_token(panel_email, panel_pass, panel_key)
    if not TOKEN[0]:
      return jsonify({'msg': TOKEN[1]}), 403
    TOKEN = TOKEN[1]['idToken']

    email_password_pairs = request.form.get('email_password_pairs').replace('\r', '').split('\n')
    email_password_pairs = [{'email': item.split(':')[0], 'password': item.split(':')[1]} for item in email_password_pairs if item != '']

    op_count = len(email_password_pairs)
    max_workers = request.form.get('max-workers',None)
    max_workers = int(max_workers) if max_workers != '' else 10
    
    task_id = str(uuid.uuid4())
    task_status = 'running'
    task_progress = 0

    kwargs = {
      'proxies':proxies,
      'email_password_pairs': email_password_pairs,
      'op_count': op_count,
      'accounts_ref':accounts_ref,
      'tasks_ref':tasks_ref,
      'task_id':task_id,
      'max_workers': max_workers,
      'url':platform_host,
      'token': TOKEN
    }

    account_task = Thread(target=TASKS().start_add_acccounts, kwargs=kwargs)
    account_task.start()

    if account_task.is_alive():
      tasks_ref.document(task_id).set({
        'id':task_id,
        'type': 'Upload Account Operation',
        "start_time":firestore.SERVER_TIMESTAMP,
        'status': task_status,
        'progress': task_progress,
        'running':True,
        'successful':0,
        'failed':0,
        'already_present': 0,
		'banned':0,
		'proxy_error':0,
        'task_count':op_count,
        'message':'Upload account operation just started'
      })

      session['MODEL']['TASKS'] = {
        'account_task':{
          'id':task_id,
          'task_status':task_status,
          'running':True,
        }
      }
      return jsonify({'msg': 'Task started, please wait while it finishes'}), 200
    else:
      return jsonify({'msg': 'No tasks running'}), 200
  except ValueError as v_error:
    print(v_error)
    return jsonify({'msg': f'{v_error}'}), 400
  except Exception as error:
    print(error)
    return jsonify({'msg': 'error starting task'}), 500

##SWIPE PAGE
@app.route('/swipe', methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def swipe_page():
	g.page = 'swipe'

	platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
	platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
	accounts_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('accounts')
	tasks_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('tasks')
	schedules_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('schedules')
		
	schedules_query = schedules_ref.where(field_path='type',op_string='==',value='swiping').order_by('added_at', direction='DESCENDING').get()
	schedules = []
	for schedule_doc in schedules_query:
		schedule = schedule_doc.to_dict()
		schedule['id'] = schedule_doc.id
		schedule['model'] = session['MODELS'][schedule['model']]['full_name']
		schedule['platform'] = session['PLATFORMS'][schedule['platform']]['name']
		schedules.append(schedule)
	
	if len(schedules) < 1:
		return redirect(url_for('schedules', action='add-schedule', type='swiping', next='swipe'))
	
	return render_template('swipe-page.html', schedules=schedules)
	
@app.route('/start-swipe', methods=['POST'])
def swipe_page_p():
	try:
		config = request.get_json()
		job_path = config['job_path']
		Scheduler().delete(job_path)


		s_sess = config['session']
		admin_id,platform_id,model_id = s_sess['admin'],s_sess['platform'],s_sess['model']

		platforms_ref = app.config['ADMINS_REF'].document(admin_id).collection('platforms')
		accounts_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('accounts')
		configs_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('configs')
		tasks_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('tasks')
		schedules_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('schedules')

		platform = platforms_ref.document(platform_id).get().to_dict()

		panel_creds = app.config['PANEL_AUTH_CREDS'][platform['name'].lower()]
		panel_email = panel_creds['email']
		panel_pass = panel_creds['password']
		panel_key = panel_creds['key']
		panel_worker_key = panel_creds['worker_key']

		s_id = config['schedule']
		schedule_ref = schedules_ref.document(s_id)

		s_name = config['schedule_name']

		data = config['data']
		op_count = len(data['accounts'])

		duration = data['duration']
		min_wait = data['min_wait']
		max_wait = data['max_wait']
		accounts = data['accounts']

		if op_count < 1: return jsonify({'msg':'Accounts must contain at least one item'}), 400
		
		daily_percent = config.get('daily_percent')
		if daily_percent is None: return jsonify({'msg':'No swipe percentage specified'}), 400

		swipe_percent = daily_percent['swipe_percent']

		TOKEN = api.get_token(panel_email, panel_pass, panel_key)
		if not TOKEN[0]:
			return jsonify({'msg': TOKEN[1]}), 403
		TOKEN = TOKEN[1]['idToken']

		proxies  = configs_ref.document('Proxies').get().to_dict()
		if not check_values([proxies['content']]): return jsonify({'msg':'No proxies for the model in schedule session'})
		
		task_id = str(uuid.uuid4())
		payload = {
			'duration':duration,
			'swipe_right_percentage':swipe_percent,
			'min_wait': min_wait,
			'max_wait': max_wait,
			'account_ids':accounts,
			'task_id':task_id,
			'session':s_sess,
			'proxies':proxies['content']
			}

		swipe = api.send_swipes(panel_creds['url'],TOKEN,json_data=payload)
		if swipe[0] and swipe[1].status_code == 200:
			tasks_ref.document(task_id).set({
					'id':task_id,
					'type': 'Swipe Operation',
					'start_time':firestore.SERVER_TIMESTAMP,
					'status': 'running',
					'progress': 0,
					'running':True,
					'failed':0,
					'successful':0,
					'task_count':op_count,
					'schedule':s_name,
					'swipe_rights':0,
					'swipe_lefts':0,
					'message': f'Initiated a swipe operation for {s_name} day {daily_percent["day"]} and session {daily_percent["session"]}'
			})
			return jsonify({'msg': f'Swipe operation with schedule {s_name} just started for day {daily_percent["day"]} and session {daily_percent["session"]}'}), 200

		print(swipe[1])
		return jsonify({'msg': f'Swipe operation with schedule {s_name} failed, day {daily_percent["day"]}'}), 400
	
	except Exception as error:
		print(error)
		return jsonify({'msg': 'error creating scheduled task'}), 500


@app.route('/send-msg', methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def send_msg():
	return redirect('/accounts')
	g.page = 'send-msg'
	global msg_task, msg_task_id
	running = False

	platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
	platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
	accounts_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('accounts')
	tasks_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('tasks')
	schedules_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('schedules')

	task_status = {}
	msg_task_id = str(uuid.uuid4())

	if msg_task:
		if msg_task.is_alive():
			running = True

		task = tasks_ref.get().to_dict()

		if task:
			task_status = {
				'type': task['type'],
				'start_time': task['start_time'],
				'status': task['status']
			}

	return render_template('send-messages.html', running=running, task_status=task_status)
	
@app.route('/tasks',methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def show_tasks():
	g.page = 'tasks'
	tasks = []
	task = request.args.get('task')
	action = request.args.get('action')


	platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
	platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
	accounts_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('accounts')
	tasks_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('tasks')
	schedules_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('schedules')

	if (task and action) and action == 'view-task':
		task_status = tasks_ref.document(task).get()
		if task_status.exists: 
			task_status = task_status.to_dict()
			start_time = task_status['start_time'].strftime("%Y-%m-%d %H:%M:%S")
			task_status['start_time'] = start_time
			return render_template('tasks.html', task_status=task_status,action=action)
		else: 
			return redirect(url_for('show_tasks'))
		
	tasks_ref = tasks_ref.order_by('start_time', direction='DESCENDING')
	tasks_data = tasks_ref.get()

	for task_doc in tasks_data:
		task = task_doc.to_dict()
		tasks.append({
			'id':task['id'],
			'type': task['type'],
			'start_time': task['start_time'],
			'status': task['status'],
			'progress':task['progress']
		})
	return render_template('tasks.html', tasks=tasks)

@app.route('/update-schedule-task/<type>', methods=['POST'])
def update_task(type):
	try:
		report = request.get_json()
		print(report)
		s_sess,task_id = report['session'],report['task_id']

		admin_id,platform_id,model_id = s_sess['admin'],s_sess['platform'],s_sess['model']
		platform_ref = app.config['ADMINS_REF'].document(admin_id).collection('platforms').document(platform_id)
		tasks_ref = platform_ref.collection('models').document(model_id).collection('tasks')

		if type in ['swiping','swipe']:
			msg = report['result']
			passes = report['success']
			fails = report['failed']
			swipe_rights = report['swipe_right']
			swipe_lefts = report['swipe_left']
			task_status = 'Failed' if passes == 0 else 'Completed'
			tasks_ref.document(task_id).update({
						'status': task_status,
						'progress': 100,
						'running':False,
						'failed':fails,
						'successful':passes,
						'swipe_rights':swipe_rights,
						'swipe_lefts':swipe_lefts,
						'message': f'Task completed with {passes} successful swipes'
			})
			return jsonify({'msg':'task updated successfully'}),200
		
		elif type == 'account':
			accounts_ref = platform_ref.collection('models').document(model_id).collection('accounts')
			account_id = report['account_id']
			account_data = report['account_details']
				
			account_snap = accounts_ref.document(account_id).get()
			if account_snap.exists:accounts_ref.document(account_id).update(account_data)
			else:accounts_ref.document(account_id).set(account_data)
			
			task = tasks_ref.document(task_id).get()
			if not task.exists:raise ValueError('task id does not exist')

			task = task.to_dict()

			passes = task['successful']
			fails = task['failed']
			op_count = task['task_count']
			created_accounts = task['created_accounts']
			swipe_configs = task['swipe_configs']

			msg = f'{passes} account of {op_count} created successfully and {op_count - (passes+fails)} waiting to be created'
			if account_data['status'] == 'CREATION_ERROR':
				fails+=1
				msg = f'{fails} account of {op_count} failed and {op_count - (fails+passes)} waiting to be created'
			elif account_data['status'] in ['FULL','NO_FACIAL']:
				passes += 1
				created_accounts.append(account_id)
				msg = f'{passes} account of {op_count} created successfully and {op_count - (passes+fails)} waiting to be created'
			elif account_data['status'] == 'PROXY_ERROR':
				msg = f'proxy error on {account_id}, retrying'

			completed = passes + fails
			if completed == op_count:
				try:
					if len(created_accounts) >= 1:
						print('\nCREATING SCHEDULES\n')
						scheduler = Scheduler()
						url = f"https://{app.config['SERVER']}/start-swipe"
						payload = {'data':{
								'accounts':created_accounts,
								'min_wait':swipe_configs['min_wait'],
								'max_wait':swipe_configs['max_wait'],
								'duration':swipe_configs['swipe_duration'] * 60},
								'schedule':swipe_configs['id'],
								'schedule_name':swipe_configs['name'],
								'session':swipe_configs['session']}
						schedule = TASKS.create_scheduler(scheduler,url,swipe_configs,payload=payload)
						print(f'\n {schedule[1]} \n')
						if schedule[0]:msg += '\n\nSchedule created for successful accounts'
						else: print(schedule[1])
				except Exception as error:
					print(error)
					msg += '\n\nError creating schedule.'
				msg = f'{passes} account of {op_count} created successfully and {op_count - (passes+fails)}'
				tasks_ref.document(task_id).update({
				'status':'failed' if passes == 0 else 'completed',
				'running':False,
				'message':msg,
				'successful':passes,
				'failed': fails,
				'created_accounts':created_accounts,
				'progress':(completed / op_count) * 100
				})
			else:
				tasks_ref.document(task_id).update({
				'running':False,
				'message':msg,
				'successful':passes,
				'failed': fails,
				'created_accounts':created_accounts,
				'progress':(completed / op_count) * 100
				})

			return jsonify({'msg':'task updated successfully'}),200
	except ValueError as error:
		print(error)
		return jsonify({'msg':f'{error}'}),400
	except Exception as error:
		print(error)
		return jsonify({'msg':'error updating task'}), 500

@app.route('/account-configs',methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def get_configuration():
	g.page = 'account-configs'
	platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
	platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
	configs_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('configs')
	panel_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]

	working_cities = ''
	with open(panel_creds['cities_file'],'r') as f:
		working_cities = f.read()

	configs_snap = configs_ref.get()
	model_configs = []
	for config in configs_snap:
		config = config.to_dict()
		content = ''
		for c in config['content']:
			content += ''.join(c) + '\n' if config['title'].lower() != 'biographies' else ''.join(c) + '\n\n'
		config['content'] = content
		model_configs.append(config)
	session['MODEL']['CONFIGS'] = model_configs
	return render_template('accounts-config.html',configs=session['MODEL']['CONFIGS'],working_cities=working_cities)

@app.route('/account-configs',methods=['POST'])
@login_required
@blocked
@check_platform
@check_model
def update_file_content():
	try:
		platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
		platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
		configs_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('configs')
		panel_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]

		data = request.get_json()
		title = data['title']
		new_content = str(data['content']).strip()

		if not check_values([new_content]): raise ValueError(f'{title} is empty')

		new_content = new_content.split('\n') if title.lower() != 'biographies' else new_content.split('\n\n')
		if title.lower() == 'cities':
			working_cities = ''
			with open(panel_creds['cities_file'],'r') as f:
				working_cities = f.read()

			for city in new_content:
				if city.strip().replace('\n','') not in working_cities.split('\n'):
					new_content.remove(city)
		elif title.lower() == 'proxies':
			if not check_proxies_format(new_content):
				raise ValueError('proxies not in the right format')

		configs = {'title':title,'content':new_content}
		configs_ref.document(title).set(configs)

		configs_snap = configs_ref.get()
		model_configs = {}
		for config in configs_snap:
			model_configs.update({config.to_dict()['title']:config.to_dict()})
		session['MODEL']['CONFIGS'] = model_configs

		return jsonify({'message': 'File content updated successfully.'}), 200
	
	except ValueError as error:
		return jsonify({'message': f'{error}'}), 400
	except Exception as error:
		print(error)
		return jsonify({'message': 'File content update unsuccessful.'}), 500

@app.route('/upload-images/<type>/<category>',methods=['POST'])
@login_required
@blocked
@check_platform
@check_model
def upload_image(type, category):
	try:
		platform_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]
		msg = ''
		uploaded = []
		platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
		platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
		images_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('images')
		
		if category == 'upload':
			image_list = request.get_json()['data']
			if not check_values(image_list):raise ValueError('No image uploaded, supply at least one image file')

			def _upload(bucket, filename, image,image_type,image_id,image_pose,_bucket_name):
				blob = bucket.blob(filename)
				blob.metadata = {
					"used": "0"
				}
				blob.upload_from_string(image,content_type=image_type)
				image_url = f'https://storage.googleapis.com/{_bucket_name}/{filename}'
				images_ref.document(image_id).set({'image':image_url,'type':type,'category':category,'pose':image_pose})
				uploaded.append(image_url)
			threads = []
			_bucket_name = platform_creds['images_bucket'] if type != 'verification' else platform_creds['v_images_bucket']
			bucket = Storage.bucket(_bucket_name)
			sub_list = sublist(image_list, 20)

			for chunk in sub_list:
				for image in chunk:
					image_id = str(uuid.uuid4())
					filename = f"{session['ADMIN']['id']}/{session['PLATFORM']['id']}/{session['MODEL']['id']}/{image_id}.jpeg"
					image_byte = base64.b64decode(image['url'].split(',')[1])
					xtension = image['name'].split('.')
					image_type = f'image/{xtension[-1]}'
					image_pose = image['pose']
					thread = Thread(target=_upload, args=(bucket, filename, image_byte,image_type,image_id,image_pose,_bucket_name))
					threads.append(thread)
					thread.start()
				for thread in threads:
					thread.join()
			msg = f'{len(uploaded)} images uploaded successfully'
		
		elif category == 'gdrive':
			image_list = request.form.get('data')
			image_list = image_list.split(',')
			if not check_values([image_list]):raise ValueError('No image uploaded, supply at least one image file')
			type = request.form.get('image-type')
			image_pose = request.form.get('pose')

			def _upload(bucket, filename, image,image_type,image_id,image_pose,_bucket_name):
				blob = bucket.blob(filename)
				blob.metadata = {
					"used": "0"
				}
				blob.upload_from_string(image,content_type=image_type)
				image_url = f'https://storage.googleapis.com/{_bucket_name}/{filename}'
				images_ref.document(image_id).set({'image':image_url,'type':type,'category':category,'pose':image_pose})
				uploaded.append(image_url)
			threads = []
			_bucket_name = platform_creds['images_bucket'] if type != 'verification' else platform_creds['v_images_bucket']
			bucket = Storage.bucket(_bucket_name)
			sub_list = sublist(image_list, 20)

			for chunk in sub_list:
				for image in chunk:
					image_id = str(uuid.uuid4())
					filename = f"{session['ADMIN']['id']}/{session['PLATFORM']['id']}/{session['MODEL']['id']}/{image_id}.jpeg"
					image_data = get_image_from_gdrive(image)
					if not image_data[0]:
						print(image_data[1])
						continue
					image_byte = image_data[1]
					xtension = '.jpeg'
					image_type = f'image/jpg'
					thread = Thread(target=_upload, args=(bucket, filename, image_byte,image_type,image_id,image_pose,_bucket_name))
					threads.append(thread)
					thread.start()
				for thread in threads:
					thread.join()

		
			msg = f'{len(uploaded)} images uploaded successfully'
		if len(uploaded) < 1:raise ValueError('No image uploaded, could be network error, please try again')
		return jsonify({'msg': msg, 'data':uploaded}), 200
	
	except ValueError as v_error:
		return jsonify({'msg':f'{v_error}'}),400
	except Exception as error:
		print(error)
		return jsonify({'msg': 'Image upload unsuccessful'}), 500

@app.route('/images', methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def redirect_images():
	return redirect('images/profile')

@app.route('/images/<type>', methods=['GET'])
@login_required
@blocked
@check_platform
@check_model
def images(type):
	platform_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]
	g.page = 'images'
	g.poses = platform_creds['poses']
	try:
		action = request.args.get('action')
		pose = request.args.get('pose')

		platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
		platform_id,model_id = session['PLATFORM']['id'],session['MODEL']['id']
		images_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('images')
		
		if action == 'add-drive':
			return render_template('images.html', type=type, action=action)
		
		page = int(request.args.get('page', 1))
		limit = int(request.args.get('limit', 10))
		model_id = session.get('MODEL')['id']
		total_query = {}
		if pose:
			total_query = images_ref.where(field_path='type', op_string='==', value=type).where(field_path='pose', op_string='==', value=pose)
		else:
			total_query = images_ref.where(field_path='type', op_string='==', value=type)
		
		total = len(list(total_query.get()))
		offset = (page - 1) * limit if page <= total else 0

		query = total_query.limit(limit).offset(offset).get()
		
		images = [{'img': doc.to_dict()['image'], 'id': doc.id, 'type': doc.to_dict()['type'],'cat':doc.to_dict()['category']} for doc in query]
		sum = min((offset) + len(images), total)

		return render_template('images.html', images=images, page=page, limit=limit, total=total, type=type,active_pose=pose, sum=sum)
	
	except Exception as error:
		print(error)
		return render_template('images.html')

@app.route('/delete-image', methods=['POST'])
@login_required
@blocked
@check_platform
@check_model
def delete_item():
	try:
		platform_creds = app.config['PANEL_AUTH_CREDS'][session['PLATFORM']['name'].lower()]
		platforms_ref = app.config['ADMINS_REF'].document(session['ADMIN']['id']).collection('platforms')
		admin_id,platform_id,model_id = session['ADMIN']['id'],session['PLATFORM']['id'],session['MODEL']['id']
		images_ref = platforms_ref.document(platform_id).collection('models').document(model_id).collection('images')
		
		image_list = request.get_json()['data']
		if not check_values([image_list]):raise ValueError('No image uploaded, supply at least one image file')
		sub_list = sublist(image_list, 20)
		threads = []
		def _delete(image,bucket):
			image_id = image['id']
			image_upload_type = image['upload_type']
			image_name = f'{admin_id}/{platform_id}/{model_id}/{image["name"]}'
			image_blob = bucket.blob(image_name)
			image_blob.delete()
			images_ref.document(image_id).delete()
		for chunk in sub_list:
			for image in chunk:
				try:
					type = image['type']
					_bucket_name = platform_creds['images_bucket'] if type != 'verification' else platform_creds['v_images_bucket']
					bucket = Storage.bucket(_bucket_name)
					if not check_values([image.get('upload_type'),image.get('id')]):
						raise ValueError('Image does not exist or is not of supported type')
					thread = Thread(target=_delete, args=(image,bucket))
					threads.append(thread)
					thread.start()
				except Exception as error:
					print(error)
					return jsonify({'msg':"couldn't delete image"}), 400
			for thread in threads:
				thread.join()

		return jsonify({'msg':'image(s) deleted successfully'}), 200
	
	except ValueError as error:
		return jsonify({'msg': f'{error}'}), 400
	except TypeError as error:
		print(error)
		return jsonify({'msg': f'error deleting image'}), 500
	except Exception as error:
		print(error)
		return jsonify({'msg': f'error deleting image'}), 500
	
@app.route(f'/files/<type>/<folder>/<subfolder>/<types>/<file>', methods=['GET'])
def serve_files(type,folder,subfolder,types,file): 
	try:
		if isfile(os.path.abspath(f'{folder}/{subfolder}/{types}/{file}')):
			filename  = os.path.abspath(f'{folder}/{subfolder}/{types}/{file}')
		if type == 'image':
			return send_file(filename, mimetype='image/jpeg')
		return send_file(filename)
	except:
		return abort(404)

if __name__ == "__main__":
	app.run()