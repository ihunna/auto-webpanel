import os, json, sys,uuid,sqlite3,base64,io,ast,httpx,time,re,shutil
from os import listdir
from os.path import isfile
from datetime import datetime, timedelta
from PIL import Image
from tempfile import mkdtemp

from threading import Thread
from uszipcode import SearchEngine
from dotenv import load_dotenv,dotenv_values, set_key
from functools import wraps

from flask import Flask, flash, redirect, render_template,send_file, abort, url_for,request, session,jsonify,g,send_from_directory
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(root, '..'))

parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app_folder = os.path.join(parent_folder,'app')
accounts_file = os.path.join(parent_folder, 'accounts.json')
zip_file = os.path.join(parent_folder, 'zipcodes.txt')
env_path = os.path.join(parent_folder, '.env')
database_file = os.path.join(app_folder,'okcupid.db')
image_folder = os.path.join(app_folder,'images')


lander_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "./static"))
data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "./data"))

names_file = os.path.join(data_folder, 'names.txt')
proxies_file = os.path.join(data_folder, 'proxies.txt')
email_password__file = os.path.join(data_folder, 'email_passwords.txt')
user_agents_file = os.path.join(data_folder, 'user_agents.txt')
biographies_file = os.path.join(data_folder, 'biographies.txt')
zip_file = os.path.join(data_folder, 'zipcodes.txt')

file_paths = [
        ('Names', names_file),
        ('Proxies', proxies_file),
        ('Email and Password', email_password__file),
        ('User Agents', user_agents_file),
        ('Biographies', biographies_file),
		('zip_codes',zip_file)
	    ]

load_dotenv(env_path)
CAPTCHA1KEY=os.getenv('CAPTCHA1KEY')
CAPTCHA2KEY=os.getenv('CAPTCHA2KEY')
SMSV1=os.getenv('SMSV1')
SMSV2=os.getenv('SMSV2')
PASSKEY=os.getenv('ADMIN_SECRET')
S_LINK=os.getenv('SIGNUP_LINK')

keys = [CAPTCHA1KEY, CAPTCHA2KEY, SMSV1, SMSV2]
KEY= os.getenv('KEY')
session_key = os.getenv('SESSION_KEY')

def get_token(email:str,password:str,key:str):
	url = f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={key}'
	json_data = {
		"email": email,
		"password": password,
		"returnSecureToken": True
	}
	token = httpx.post(url,json=json_data)
	if token.status_code == httpx.codes.OK:return True, token.json()
	else: return False, token.text

# Configure application
app = Flask(__name__)
app.debug = True

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


app.config["SESSION_TYPE"] = "filesystem"
app.config["SECRET_KEY"] = session_key.encode()
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)
Session(app)

app.config['DATABASE'] = database_file
app.config['IMAGE_FOLDER'] = image_folder
app.config['LANDER'] = os.path.join(lander_folder,'index.html')
app.config['PLATFORMS']:dict = {}
app.config['ADMINS']:dict = {}
app.config['PASS_KEY'] = PASSKEY
app.config['S_LINK'] = S_LINK
app.config['ENV_VALUES'] = dotenv_values(env_path)

def conn():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = sqlite3.connect(app.config['DATABASE'])
		db.execute('PRAGMA foreign_keys = ON')
		cursor = db.cursor()

		#create platforms table
		cursor.execute('''CREATE TABLE IF NOT EXISTS platforms
		(id TEXT PRIMARY KEY,user_id TEXT,admin TEXT,name TEXT,added_at DATETIME DEFAULT CURRENT_TIMESTAMP)
		''')

		#create models table
		cursor.execute('''CREATE TABLE IF NOT EXISTS models
		(id TEXT PRIMARY KEY,user_id TEXT,full_name TEXT,username TEXT,swipe_percent TEXT,socials TEXT,added_at DATETIME DEFAULT CURRENT_TIMESTAMP)
		''')

		#create admins table
		cursor.execute('''CREATE TABLE IF NOT EXISTS admins
			(id TEXT PRIMARY KEY,full_name TEXT,email TEXT,password TEXT,
			role TEXT,status TEXT,created_at DATETIME DEFAULT CURRENT_TIMESTAMP)
			''')
		
		#create accounts table
		cursor.execute('''
					CREATE TABLE IF NOT EXISTS accounts
					(id TEXT PRIMARY KEY,
					user_id TEXT,
					data TEXT,
					email TEXT,
					model TEXT,
					notifications TEXT,
					swipes INTEGER,
					messages INTEGER,
					likes INTEGER,
					timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)
					''')
		#create tasks table
		cursor.execute(''' CREATE TABLE IF NOT EXISTS tasks
		(id TEXT PRIMARY KEY,user_id TEXT,model TEXT,type TEXT,start_time DATETIME DEFAULT CURRENT_TIMESTAMP, status TEXT, progress INTEGER)''')

		#create images table
		cursor.execute('''CREATE TABLE IF NOT EXISTS images
		(id TEXT PRIMARY KEY, data TEXT,type TEXT,model TEXT,user_id TEXT, status TEXT)
		''')
	
	return db

@app.teardown_appcontext
def close_db(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()

def login_required(func):
	@wraps(func)
	def decorated_function(*args, **kwargs):
		if 'ADMIN' not in session:
			if request.method == 'GET':
				return redirect(url_for('login'))
			elif request.method in ['POST', 'DELETE', 'PUT', 'PATCH']:
				return jsonify({'msg': 'you have to be logged in'}), 403
		return func(*args, **kwargs)
	return decorated_function

def check_platform(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		if 'PLATFORM' not in session:
			session['CURRENT_URL'] = request.path
			if request.method == 'GET':
				return redirect(url_for('index'))
			elif request.method in ['POST','DELETE','PUT','PATCH']:
				return jsonify({'msg':'no platfrom chosen'}),403
		return func(*args, **kwargs)
	return wrapper

def check_model(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		session['CURRENT_URL'] = request.path
		if 'MODEL' not in session:
			if request.method == 'GET':
				return redirect(url_for('models'))
			elif request.method in ['POST','DELETE','PUT','PATCH']:
				return jsonify({'msg':'no model chosen'}),403
		return func(*args, **kwargs)
	return wrapper

def check_super(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		if session['ADMIN']['role'] == 'admin':
			if request.method == 'GET':
				return redirect(f'/admins?admin={session["ADMIN"]["id"]}&action=admin-settings')
			elif request.method in ['POST','DELETE','PUT','PATCH']:
				return jsonify({'msg':'You are not authorized for this action'}),403
		return func(*args, **kwargs)
	return wrapper

def validate_email(email):
	pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
	return re.match(pattern, email)

def validate_password(password):
	pattern = r'^(?=.*\d)(?=.*[a-zA-Z]).+$'
	return re.match(pattern, password)

def validate_passkey(passkey):
	if passkey and passkey == app.config['PASS_KEY']:return True
	return False

account_task = None
account_task_start_time = None
account_task_id = None
account_task_status = "Not started"

swipe_task = None
swipe_task_start_time = None
swipe_task_status = "Not started"

msg_task = None
msg_taskstart_time = None
msg_task_status = "Not started"


