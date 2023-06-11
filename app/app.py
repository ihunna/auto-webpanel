from app_actions import start_task
from app_configs import *


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
def redirect_dash():
	return redirect('/platforms')

@app.route('/platforms',methods=['GET'])
@login_required
def index():
	g.page = 'platforms'
	platform_id = request.args.get('platform')
	action = request.args.get('action')
	if not platform_id and not action:
		db = conn()
		cursor = db.cursor()
		cursor.execute('''SELECT * FROM platforms ORDER BY added_at DESC''')
		platforms = cursor.fetchall()

		platforms = [{
			'id':platform[0],
			'name':str(platform[3]).upper(),
			'added_by':platform[2],
			'added_at':platform[4]
		} for platform in platforms]

		for platform in platforms:app.config['PLATFORMS'].update({platform['id']:platform})
		return render_template("index.html",platforms=platforms)
	
	elif action == 'add-platform':
		return render_template("index.html",action=action)
	
	elif action == 'delete-platform':
			platform_ids = [p['id'] for p in list(app.config['PLATFORMS'].values())]
			if platform_id in platform_ids:
				db = conn()
				cursor = db.cursor()
				cursor.execute('''DELETE FROM platforms WHERE id =?''',(platform_id,))
				db.commit()
				if platform_id in app.config['PLATFORMS']:del app.config['PLATFORMS'][platform_id]
				if session.get('PLATFORM') and platform_id == session.get('PLATFORM')['id']: 
					del session['PLATFORM']
			return redirect('/dashboard')
	else:
		session['PLATFORM'] = app.config['PLATFORMS'].get(platform_id)
		current_url = session.get('CURRENT_URL')
		url = str(current_url) if current_url is not None else '/accounts'
		return redirect(url)

@app.route('/add-platform', methods=['POST'])
@login_required
def add_platform():
	try:
		platform_name = request.form.get('platform-name')
		user_id = session.get('ADMIN')['id']
		admin_name = session.get('ADMIN')['full_name']
		platform_names = [p['name'] for p in list(app.config['PLATFORMS'].values())]
		if str(platform_name).upper() not in platform_names:
			db = conn()
			cursor = db.cursor()
			cursor.execute('''INSERT INTO platforms
			(id,name,user_id,admin) VALUES (?,?,?,?)
			''',(str(uuid.uuid4()),platform_name,user_id,admin_name))
			db.commit()

			return jsonify({'msg':'platform added successfully'}),200
		return jsonify({'msg':'platform already exists'}),400
	except Exception as error:
		print(error)
		return jsonify({'msg':'error adding platform'}),500

@app.route('/admins',methods=['GET'])
@login_required
def admins():
	g.page = 'admins'
	action = request.args.get('action')
	db = conn()
	cursor = db.cursor()
	if  action and action == 'admin-settings':
		admin = session.get('ADMIN')
		admin_id = admin['id']
		
		cursor.execute('SELECT COUNT(*) FROM images WHERE user_id=?',
		(admin_id,))
		admin_images = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM accounts WHERE user_id=?',
		(admin_id,))
		admin_accounts = cursor.fetchone()[0]

		cursor.execute('SELECT COUNT(*) FROM tasks WHERE user_id=?',
		(admin_id,))
		admin_tasks = cursor.fetchone()[0]
		return render_template('admins.html', action = action,admin=admin,
			admin_images=admin_images,admin_accounts=admin_accounts,admin_tasks=admin_tasks)
	
	elif  action and action == 'edit-signup-configs':
		admin = session.get('ADMIN')
		return render_template('admins.html', action = action,admin=admin)
	
	if session['ADMIN']['role'] != 'admin':
		page = int(request.args.get('page', 1))
		limit = int(request.args.get('limit', 20))

		cursor.execute('SELECT COUNT(*) FROM admins')
		total = cursor.fetchone()[0]

		offset = (page - 1) * limit if page <= total else 0

		cursor.execute('''SELECT * FROM admins ORDER BY created_at DESC LIMIT ? OFFSET ?''',(limit,offset))
		admins = cursor.fetchall()

		admins = [{
			'id':admin[0],
			'full_name':admin[1],
			'email':admin[2],
			'password':admin[3],
			'role':admin[4],
			'status':admin[5],
			'created_at':admin[6]
		}for admin in admins]

		for admin in admins:app.config['ADMINS'].update({admin['id']:admin})
		admin_id = session.get('ADMIN')['id']
		session['ADMIN'] = app.config['ADMINS'][admin_id]
		sum = min((offset) + len(admins), total)
		return render_template('admins.html',admins=admins,page=page,sum=sum, limit=limit,total=total)

	return redirect(f'admins?admin={session["ADMIN"]["id"]}&action=admin-settings')


@app.route('/admins/<action>', methods=['POST'])
@login_required
def admin(action):
	try:
		db = conn()
		cursor = db.cursor()

		if action =='admin-settings':
			full_name = request.form.get('admin-fullname')
			email = request.form.get('admin-email')
			emails = [e['email'] for e in list(app.config['ADMINS'].values())]
			admin_id = session.get('ADMIN')['id']

			if email not in emails:
				cursor.execute('''UPDATE admins 
				SET full_name=?,email=? WHERE id=? 
				''',(full_name,email,admin_id))
				db.commit()
			else:
				cursor.execute('''UPDATE admins 
				SET full_name=? WHERE id=? 
				''',(full_name,admin_id))
				db.commit()
			return jsonify({'msg':'admin updated successfully'}),200
		
		elif action == 'make-super':
			op_admin_id = request.get_json()['data'][0]['admin_id']
			op_admin = app.config['ADMINS'][op_admin_id]
			op_admin_status = op_admin['status']

			admin = session.get('ADMIN')
			if admin['role'] == 'super-admin' and (op_admin_status == 'active' and admin['id'] != op_admin_id):
				cursor.execute('''UPDATE admins SET role =? WHERE id =?''',('super-admin',op_admin_id))
				db.commit()
				return jsonify({'msg':'user updated to super admin'}),200
			return jsonify({'msg':'not authorized'}),403

		elif action == 'block':
			op_admin_id = request.get_json()['data'][0]['admin_id']
			op_admin = app.config['ADMINS'][op_admin_id]
			op_admin_status = op_admin['status']
			admin = session.get('ADMIN')
			if admin['role'] == 'super-admin' and (op_admin_status == 'active' and admin['id'] != op_admin_id):
				cursor.execute('''UPDATE admins SET status =?, role=? WHERE id =?''',('blocked','admin',op_admin_id,))
				db.commit()
				return jsonify({'msg':'user blocked'}),200
			return jsonify({'msg':'not authorized'}),403

		elif action == 'unblock':
			op_admin_id = request.get_json()['data'][0]['admin_id']
			print(app.config['ADMINS'])
			op_admin = app.config['ADMINS'][op_admin_id]
			op_admin_status = op_admin['status']
			admin = session.get('ADMIN')
			if admin['role'] == 'super-admin' and (op_admin_status == 'blocked' and admin['id'] != op_admin_id):
				cursor.execute('''UPDATE admins SET status =? WHERE id =?''',('active',op_admin_id))
				db.commit()
				return jsonify({'msg':'user unblocked'}),200
			return jsonify({'msg':'not authorized'}),403
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
				return jsonify({'msg':'configs updated successfully'}),200
			else:return jsonify({'msg':'Unauthorized'}),403


	except Exception as error:
		print(error)
		return jsonify({'msg':'error updating admin'}),500


@app.route('/models', methods = ['GET'])
@login_required
@check_platform
def models():
	g.page = 'models'
	model_id = request.args.get('model')
	action = request.args.get('action')
	if not model_id and not action:
		db = conn()
		cursor = db.cursor()
		cursor.execute('''SELECT * FROM models WHERE user_id=? ORDER BY added_at DESC''', (session['ADMIN']['id'],))
		models = cursor.fetchall()
		models = [{
			'id':model[0],
			'full_name':str(model[2]),
			'username':model[3],
			'added_at':model[6],
			'swipe_percent':model[4],
			'socials':ast.literal_eval(model[5])
		} for model in models]
		
		for model in models:session['MODELS'].update({model['id']:model})
		return render_template('models.html',models=models)
	
	elif action == 'add-model':
			g.page = 'add-model'
			return render_template('models.html',action=action)
	else:
		model_ids = [u['id'] for u in list(session['MODELS'].values())]
		if model_id in model_ids:
			if action == 'set-model':
				session['MODEL'] = session['MODELS'][model_id]
				current_url = session.get('CURRENT_URL')
				url = str(current_url) if current_url is not None else '/models'
				return redirect(url)
			elif action == 'edit-model':
				model=app.config['MODELS'][model_id]
				admin_id = session.get('ADMIN')['id']
				db = conn()
				cursor = db.cursor()
				cursor.execute('SELECT COUNT(*) FROM images WHERE model=? AND user_id=?',
			   	(model_id, admin_id))
				model_images = cursor.fetchone()[0]

				cursor.execute('SELECT COUNT(*) FROM accounts WHERE model=? AND user_id=?',
			   	(model_id,admin_id))
				model_accounts = cursor.fetchone()[0]

				cursor.execute('SELECT COUNT(*) FROM tasks WHERE model=? AND user_id=?',
			   	(model_id,admin_id))
				model_tasks = cursor.fetchone()[0]

				return render_template('models.html',model=model,action=action,
			   	model_images=model_images,model_accounts=model_accounts,model_tasks=model_tasks)
		
			elif action == 'delete-model':
				db = conn()
				cursor = db.cursor()
				cursor.execute('''DELETE FROM models WHERE id =?''',(model_id,))
				db.commit()

				for folder in os.listdir(image_folder):
					if folder == model_id:
						shutil.rmtree(f'{image_folder}\\{model_id}')
			
				del app.config['MODELS'][model_id]
				if session.get('MODEL') and model_id == session.get('MODEL')['id']: 
					del session['MODEL']
				return redirect('/models')
		return redirect('/models')
		
@app.route('/models/<action>', methods=['POST']) #modified
def model(action):
	try:
		if action == 'add-model':
			full_name = request.form.get('model-fullname')
			username = request.form.get('model-uname')
			swipe_percent = request.form.get('model-swipe-percent')
			socials = request.form.get('model-socials')
			socials = socials.split(',')

			socials = request.form.get('model-socials')
			socials = socials.split(',')	
			model_socials = [
				{
					"platform":social.split('/')[0],
					"handle":social.split('/')[1]
				} for social in socials if social.strip()]

			print(model_socials)

			user_id = session.get('ADMIN')['id']
			model_id = str(uuid.uuid4())

			usernames = [u['username'] for u in list(session.get('MODELS').values())]
			if username not in usernames:
				location = os.path.join(app_folder,'images',model_id)
				if os.path.exists(location):
					return jsonify({'msg': 'Folder already exists'}), 400
				
				db = conn()
				cursor = db.cursor()

				cursor.execute('''INSERT INTO models
				(id,user_id,full_name,username,swipe_percent,socials) VALUES (?,?,?,?,?,?)
				''',(model_id,user_id,full_name,username,swipe_percent,str(model_socials)))
				db.commit()

				cursor.execute('''SELECT * FROM models WHERE id =?''',(model_id,))
				model = cursor.fetchone()

				# Create the main folder
				os.makedirs(location)

				# Create the 'profile' and 'images' subfolders
				profile_folder = os.path.join(location, "profile")
				os.makedirs(profile_folder)

				images_folder = os.path.join(location, "images")
				os.makedirs(images_folder)
				if model:
					session['MODELS'].update({model_id:{
						'id':model[0],
						'full_name':str(model[2]),
						'username':model[3],
						'added_at':model[6],
						'swipe_percent':model[4],
						'socials':ast.literal_eval(model[5])
					}})
				else:return jsonify({'msg':'error adding model'}),200

				return jsonify({'msg':'model added successfully'}),200
			return jsonify({'msg':'model already exists'}),400
		
		elif action == 'edit-model':
			full_name = request.form.get('model-fullname')
			username = request.form.get('model-uname')
			swipe_percent = request.form.get('model-swipe-percent')
			model_id = request.form.get('model-id')

			socials = request.form.get('model-socials')
			socials = socials.split(',')	
			model_socials = [
				{
					"platform":social.split('/')[0],
					"handle":social.split('/')[1]
				} for social in socials if social.strip()]
			db = conn()
			cursor = db.cursor()
			cursor.execute('''UPDATE models 
			SET full_name=?,username=?,swipe_percent =?, socials=? WHERE id=? AND user_id =? 
			''',(full_name,username,swipe_percent,str(model_socials),model_id,session['ADMIN']['id']))
			db.commit()
			return jsonify({'msg':'model updated successfully'}),200
	except Exception as error:
		print(error)
		return jsonify({'msg':'error updating model'}),500


@app.route('/signup',methods=['POST','GET'])
def signup():
	if request.method == 'GET':return redirect(url_for('login'))
	return jsonify({'msg':'Not authorized'}),403

@app.route(f'/signup/<key>', methods=['GET'])
def signup_page(key):
	g.page = 'signup'
	if key and key == app.config['S_LINK']:
		if 'ADMIN' not in session:return render_template('signup.html')
		else:return redirect(url_for('index'))
	return abort(404)


@app.route(f'/adminonlyallowedtosignup__________',methods=['POST'])
def do_signup():
	try:
		if request.method == 'GET':return redirect(url_for('login'))
		db = conn()
		cursor = db.cursor()

		full_name = request.form.get('full-name')
		email = request.form.get('email')
		password = request.form.get('password')
		passkey = request.form.get('passkey')

		uid = str(uuid.uuid4())
		role = 'admin'
		status = 'active'
		if not validate_passkey(passkey):return jsonify({'msg':"you're not allowed"}),403
		
		elif not full_name or not email or not password:
			return jsonify({'msg':'some entries are empty, fill all fields'}),400
		
		elif not validate_email(email):return jsonify({'msg':'not a valid email'}),400
		
		elif len(str(password)) < 8:return jsonify({'msg':'password must be 8 or more chars'}),400
		elif not validate_password(password):
			return jsonify({'msg':'password must contain 8 or more chars of laters and digits'}),400
		password = generate_password_hash(password)

		cursor.execute('''SELECT email FROM admins WHERE email =?''',(email,))
		_email = cursor.fetchone()

		if _email:return jsonify({'msg':'email already exists'}),400

		cursor.execute('''INSERT INTO admins (id,full_name,email,password,role,status)
		VALUES (?,?,?,?,?,?)''',(uid,full_name,email,password,role,status))
		db.commit()

		cursor.execute('''SELECT * FROM admins WHERE id =?''',(uid,))
		result = cursor.fetchone()
		admin = {
			'id':result[0],
			'full_name':result[1],
			'email':result[2],
			'password':result[3],
			'role':result[4],
			'status':result[5],
			'created_at':result[6]
		}
		app.config['ADMINS'].update({admin['id']:admin})

		return jsonify({'msg':admin}),200
	except Exception as error:
		print(error)
		return abort(500)
	
@app.route('/login',methods=['GET','POST'])
def login():
	try:
		if request.method == 'GET':
			if 'ADMIN' not in session:return render_template('login.html')
			else:return redirect(url_for('index'))
		elif request.method == 'POST':
			db = conn()
			cursor = db.cursor()

			email = request.form.get('email')
			password = request.form.get('password')

			if not email or not password:
				return jsonify({'msg':'some entries are empty, fill all fields'}),400
			
			cursor.execute('SELECT * FROM admins WHERE email = ?', (email,))
			result = cursor.fetchone()
			if result:
				admin = {
					'id':result[0],
					'full_name':result[1],
					'email':result[2],
					'password':result[3],
					'role':result[4],
					'status':result[5],
					'created_at':result[6]
				}
				hashed_password = admin['password']
				if check_password_hash(hashed_password, password):
					session['ADMIN'] = admin
					session['MODELS']:dict = {}
					return jsonify({'msg':'login successful'}),200
				else:return jsonify({'msg':'wrong password'}),403
			else:return jsonify({'msg':'user does not exist'}),403
			

	except Exception as error:
		print(error)
		abort(500)

@app.route('/accounts',methods=['GET'])
@login_required
@check_platform
@check_model
def accounts():
	g.page = 'accounts'
	accounts = []
	all_accounts = []
	server = url_for('index', _external=True)

	'''
	This is to see the accounts added to the db.
	The ones presented are from the json file.
	'''
	db = conn()
	cursor = db.cursor()

	cursor.execute('SELECT COUNT(*) FROM accounts WHERE user_id=?',
		(session['ADMIN']['id'],))
	total = cursor.fetchone()[0]

	page = int(request.args.get('page', 1))
	limit = int(request.args.get('limit', 20))
	offset = (page - 1) * limit if page <= total else 0

	cursor.execute('''SELECT * FROM accounts WHERE user_id =? ORDER BY timestamp DESC LIMIT ? OFFSET ?''',
					(session['ADMIN']['id'],limit,offset))
	accounts = cursor.fetchall()
	sum = min((offset) + len(accounts), total)
	return render_template("accounts.html",accounts=accounts,
			sum=sum,total=total,page=page,limit=limit)

@app.route('/account-page',methods=['GET'])
@login_required
@check_platform
@check_model
def account_page():
	g.page = 'accounts'
	id = request.args.get('account')
	action = request.args.get('action')
	is_account = False
	if id:
		account = {}
		images = []
		with open(accounts_file,'r',encoding='utf-8') as f:
			accounts = json.load(f)
			if id in accounts.keys():
				is_account = True
				account = accounts[id]
				matches = account['user_data']['data']['me']['stack']
				matches = json.dumps(matches, separators=(',', ':'),ensure_ascii=False)
				i = 0
				if 'photos' in account['user_data']['data']['me'].keys():
					for image in  account['user_data']['data']['me']['photos']:
						if i >=3:break
						images.append(image)
				else:images.append(account['user_data']['data']['me']['primaryImage'])
		
		if is_account:
			if action == 'map':
				return render_template('account-page.html',account=account,images=images,action=action)
			elif action == 'edit-account':
				return render_template('account-page.html',account=account,images=images,action=action)
			return render_template('account-page.html',account=account,images=images,matches=matches)
		else:return redirect('/dashboard')
	return redirect('/dashboard')

@app.route('/account-page/<action>',methods=['POST'])
@login_required
@check_platform
@check_model
def account_action(action):
	try:
		if action=='edit-account':
			return jsonify({'msg': 'account updated successfully'}), 200
		elif action=='map-update':
			data = request.json['data']
			longitude = data['long']
			latitude = data['lat']
			print(longitude, latitude)

			return jsonify({'msg': 'location updated successfully'}), 200
	except:
		return jsonify({'msg': 'Error'}), 404
	
@app.route('/create-accounts',methods=['POST'])
@login_required
@check_platform
@check_model
def create_accounts():
	global account_task,account_task_id,account_task_start_time, account_task_status

	TOKEN = get_token('okcupid@atonline.com','jUX@5EH85kX0',KEY)
	if not TOKEN[0]:return jsonify({'msg': TOKEN[1]}), 403
	TOKEN = TOKEN[1]['idToken']

	op_count = int(request.form.get('op-count'))
	bio = request.form.get('bio')
	max_workers = request.form.get('max-workers') 
	max_workers = int(max_workers) if max_workers else 2

	account_task_status = 'Running'
	account_task_id = str(uuid.uuid4())

	db = conn()
	cursor = db.cursor()
	model = session['MODEL']
	admin = session['ADMIN']
	cursor.execute('''SELECT * FROM images WHERE model=? AND type=? AND user_id=?''',(model['id'],admin['id'],'profile'))
	images = cursor.fetchall()
	images = [{'id': img[0], 'links': ast.literal_eval(img[1])} for img in images]

	kwargs ={
		'op_count':op_count,
		'bio':bio,
		'max_workers':max_workers,
		'task_id':account_task_id,
		'images':images,
		'token':TOKEN
	}

	cursor.execute('''INSERT INTO tasks (id,type,status,progress) VALUES (?,?,?,?)
	''', (account_task_id, 'Account Creation Operation', account_task_status,0))
	db.commit()

	account_task = Thread(target=start_task, kwargs=kwargs)
	account_task.start()

	account_task.native_id

	if account_task.is_alive():
		return jsonify({'msg':'Task started, please wait while it finishes'}), 200
	else: 
		return jsonify({'msg':'No tasks running'}), 200

@app.route('/create-accounts',methods=['GET'])
@login_required
@check_platform
@check_model
def show_create_accounts():
	global account_task, account_task_id
	g.page = 'create-accounts'
	running = False
	task_status = {}

	if account_task:
		if account_task.is_alive():running = True
		db = conn()
		cursor = db.cursor()
		cursor.execute('''SELECT * FROM tasks WHERE id =?''',(account_task_id,))
		task = cursor.fetchone()

		task_status = {
			'type':task[3],
			'start_time':task[4],
			'status':task[5]
		}
	return render_template('create-accounts.html',running=running,task_status=task_status,
			model=session['MODEL'])

##SWIPE PAGE
@app.route('/swipe', methods=['GET'])
@login_required
@check_platform
@check_model
def swipe_page():
	g.page = 'swipe'
	global swipe_task, swipe_task_id
	running = False
	task_status = {}

	if swipe_task:
		if swipe_task.is_alive():
			running = True
		db = conn()
		cursor = db.cursor()
		cursor.execute('''SELECT * FROM tasks WHERE id =?''', (swipe_task_id,))
		task = cursor.fetchone()

		task_status = {
			'type': task[1],
			'start_time': task[2],
			'status': task[3],
			'progress': task[4]
		}
	return render_template('swipe-page.html',running=running,task_status=task_status)
	
@app.route('/swipe', methods=['POST'])
@login_required
@check_platform
@check_model
def swipe_page_p():
	global swipe_task, swipe_task_id, swipe_task_start_time, swipe_task_status

	op_count = int(request.form.get('op-count'))
	max_workers = request.form.get('max-workers')
	max_workers = int(max_workers) if max_workers else 2

	swipe_task_status = 'Running'
	swipe_task_id = str(uuid.uuid4())

	db = conn()
	cursor = db.cursor()

	## BOT LOGIC
	cursor.execute('''INSERT INTO tasks (id,type,status,progress) VALUES (?,?,?,?)
	''', (swipe_task_id, 'Swiping Operation', swipe_task_status,0))
	db.commit()
	swipe_task = Thread(target=slp)
	swipe_task.start()


	if swipe_task.is_alive():
		return jsonify({'msg': 'Task started, please wait while it finishes'}), 200
	else:
		return jsonify({'msg': 'No tasks running'}), 200


@app.route('/send-msg', methods=['GET'])
@login_required
@check_platform
@check_model
def send_msg():
	g.page = 'send-msg'
	global swipe_task, swipe_task_id
	running = False
	task_status = {}

	if swipe_task:
		if swipe_task.is_alive():
			running = True
		db = conn()
		cursor = db.cursor()
		cursor.execute('''SELECT * FROM tasks WHERE id =?''', (swipe_task_id,))
		task = cursor.fetchone()

		task_status = {
			'type':task[3],
			'start_time':task[4],
			'status':task[5]
		}
	return render_template('send-messages.html',running=running,task_status=task_status)
	

@app.route('/tasks',methods=['GET'])
@login_required
@check_platform
@check_model
def show_tasks():
	g.page = 'tasks'
	tasks = []
	db = conn()
	cursor = db.cursor()
	cursor.execute('''SELECT * FROM tasks ORDER BY start_time DESC''')
	tasks = cursor.fetchall()
	
	tasks = [{
			'type':task[3],
			'start_time':task[4],
			'status':task[5]
		} for task in tasks]
	return render_template('tasks.html',tasks=tasks)

@app.route('/account-configs',methods=['GET'])
@login_required
@check_platform
def get_configuration():
	g.page = 'account-configs'
	file_contents = {}
	for file_name, file_path in file_paths:
		try:
			with open(file_path, 'r') as file:
				file_contents[file_name] = file.read()
		except FileNotFoundError:
			return f"File not found: {file_path}"
	
	return render_template('accounts-config.html', file_contents=file_contents)

@app.route('/account-configs',methods=['POST'])
@login_required
@check_platform
def update_file_content():
	data = request.get_json()
	title = data['title']
	new_content = data['content']

	def get_file_path_based_on_title(title):
		path=None
		for key, p in file_paths:
			if key == title:
				path=p
				break
		return path
	
	path = get_file_path_based_on_title(title)
	if not path: return jsonify({'error': 'File not found.'}), 404

	else:
		with open(path, 'w') as file:
			file.write(new_content)

		return jsonify({'message': 'File content updated successfully.'}), 200

@app.route('/upload-images/<type>',methods=['POST'])
@login_required
@check_platform
@check_model
def upload_image(type):
	try:
		image_list = request.get_json()['data']
		image_urls = []
		model = session.get('MODEL')
		admin = session.get('ADMIN')

		for image in image_list:
			image_data = image['url'].split(',')[1]
			image_id = str(uuid.uuid4())
			image_name =  image_id + '.jpeg'
			save_path = os.path.join(app.config['IMAGE_FOLDER'],model['id'],type,image_name)

			with open(save_path, 'wb') as file:
				file.write(base64.b64decode(image_data))
			_data = f'/files/image/images/{model["id"]}/{type}/{image_name}'

			db = conn()
			cursor = db.cursor()
			cursor.execute('''INSERT INTO images (id,data,status,model,user_id,type) VALUES (?,?,?,?,?,?)''',
			(image_id,_data,'new',model['id'],admin['id'],type))
			db.commit()

			cursor.execute('''SELECT data FROM images WHERE id = ? AND model = ? AND user_id = ?''',
				(image_id, model['id'], admin['id']))
			images = cursor.fetchall()

		return jsonify({'msg':images}), 200
	
	except Exception as error:
		print(error)
		return jsonify({'msg':'image upload unsuccessful'}), 500


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

@app.route('/images', methods=['GET'])
@login_required
@check_platform
@check_model
def redirect_images():
	# db = conn()
	# cursor = db.cursor()

	# cursor.execute('DELETE FROM images')
	# db.commit()
	return redirect('images/profile')

@app.route('/images/<type>', methods=['GET'])
@login_required
@check_platform
@check_model
def images(type):
	g.page = 'images'
	try:
		page = int(request.args.get('page', 1))
		limit = int(request.args.get('limit', 10))
		model_id = session.get('MODEL')['id']
		admin_id = session.get('ADMIN')['id']

		db = conn()
		cursor = db.cursor()

		cursor.execute('SELECT COUNT(*) FROM images WHERE model=? AND type=? AND user_id=?',
			   (model_id, type, admin_id))
		total = cursor.fetchone()[0]

		offset = (page - 1) * limit if page <= total else 0

		cursor.execute('SELECT data FROM images WHERE model=? AND type=? AND user_id=? LIMIT ? OFFSET ?',
			   (model_id, type, admin_id, limit, offset))
		images = cursor.fetchall()
		images = [imgs[0] for imgs in images]
		sum = min((offset) + len(images), total)

		return render_template('images.html', images=images, page=page, 
			 limit=limit,total=total,type=type,sum=sum)
	except Exception as error:
		print(error)
		return render_template('images.html')

@app.route('/delete/<category>', methods=['POST'])
@login_required
@check_platform
@check_model
def delete_item(category):
	try:
		db = conn()
		cursor = db.cursor()
		payload = request.get_json()['data']
		for data in payload:
			if category == 'image':
				image_name = data['name']
				type = data['type']
				image_url = data['url']
				image_id = str(data['name']).split('.')[0]
				model = session.get('MODEL')
				admin = session.get('ADMIN')

				cursor.execute('''DELETE FROM images WHERE id =? AND
				model =? AND user_id =? AND type =?''',(image_id,model['id'],admin['id'],type))
				db.commit()


				image_path = os.path.join(app.config['IMAGE_FOLDER'],model['id'],type,image_name)

				if os.path.exists(image_path):
					os.remove(image_path)
					return jsonify({'msg': 'Image deleted successfully'}), 200
				else:
					return jsonify({'msg': 'Image not found'}), 404
	except Exception as error:
		print(error)
		return jsonify({'msg':f'error deleting {category}'}), 500

if __name__ == "__main__":
	app.run()