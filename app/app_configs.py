import os, json, sys,uuid,sqlite3,base64,io,ast,httpx,time,re,shutil,random,requests
from os import listdir
from os.path import isfile
from datetime import datetime, timedelta
from dateutil.parser import parse
from PIL import Image
from tempfile import mkdtemp

from threading import Thread
from concurrent.futures import ThreadPoolExecutor, as_completed
from uszipcode import SearchEngine
from dotenv import load_dotenv,dotenv_values, set_key
from functools import wraps

from flask import Flask, flash, redirect, render_template,send_file, abort, url_for,request, session,jsonify,g,send_from_directory
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from google.cloud import storage

from app_utils import sublist,identify_image_format


root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(root, '..'))

parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app_folder = os.path.join(parent_folder,'app')
accounts_file = os.path.join(parent_folder, 'accounts.json')
zip_file = os.path.join(parent_folder, 'zipcodes.txt')
env_path = os.path.join(parent_folder, '.env')
database_file = os.path.join(app_folder,'okcupid.db')
image_folder = os.path.join(app_folder,'images')

cred_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "firebase.json"))
lander_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "./static"))
data_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), "./data"))

names_file = os.path.join(data_folder, 'names.txt')
proxies_file = os.path.join(data_folder, 'proxies.txt')
email_password__file = os.path.join(data_folder, 'email_passwords.txt')
user_agents_file = os.path.join(data_folder, 'user_agents.txt')
biographies_file = os.path.join(data_folder, 'biographies.txt')
zip_file = os.path.join(data_folder, 'zipcodes.txt')



load_dotenv(env_path)
CAPTCHA1KEY=os.getenv('CAPTCHA1KEY')
CAPTCHA2KEY=os.getenv('CAPTCHA2KEY')
SMSV1=os.getenv('SMSV1')
SMSV2=os.getenv('SMSV2')
PASSKEY=os.getenv('ADMIN_SECRET')
S_LINK=os.getenv('SIGNUP_LINK')
GDRIVEAPI=os.getenv('GDRIVEAPI')

OKCUPID_KEY=os.getenv('OKCUPID_KEY')
OKCUPID_EMAIL=os.getenv('OKCUPID_EMAIL')
OKCUPID_PASS=os.getenv('OKCUPID_PASS')
OKCUPID_HOSTNAME=os.getenv('OKCUPID_HOSTNAME')

BADOO_KEY=os.getenv('BADOO_KEY')
BADOO_EMAIL=os.getenv('BADOO_EMAIL')
BADOO_PASS=os.getenv('BADOO_PASS')
BADOO_IMAGES_BUCKET=os.getenv('BADOO_IMAGES_BUCKET')
BADOO_V_IMAGES_BUCKET=os.getenv('BADOO_VERIFICATION_IMAGES_BUCKET')
BADOO_HOSTNAME=os.getenv('BADOO_HOSTNAME')
BADOO_WORKER_KEY=os.getenv('BADOO_WORKER_KEY')

keys = [CAPTCHA1KEY, CAPTCHA2KEY, SMSV1, SMSV2]
session_key = os.getenv('SESSION_KEY')


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
app.config['ADMINS']:dict = {}
app.config['PASS_KEY'] = PASSKEY
app.config['S_LINK'] = S_LINK
app.config['GDRIVEAPI'] = GDRIVEAPI
app.config['ENV_VALUES'] = dotenv_values(env_path)

app.config['PANEL_AUTH_CREDS'] = {
	'badoo':{
		'email':BADOO_EMAIL,
		'password':BADOO_PASS,
		'key':BADOO_KEY,
		'worker_key':BADOO_WORKER_KEY,
		'url':BADOO_HOSTNAME,
		'images_bucket':BADOO_IMAGES_BUCKET,
		'v_images_bucket':BADOO_V_IMAGES_BUCKET,
		'poses':[
			'yes_sign', 
			'rock_sign', 
			'hand_on_ear_sign', 
			'peace_sign', 
			'overhead_sign', 
			'five_left_side_sign', 
			'five_up_sign', 
			'pinky_sign']
	},
	'okcupid':{
		'email':OKCUPID_EMAIL,
		'password':OKCUPID_PASS,
		'key':OKCUPID_KEY,
		'url':OKCUPID_HOSTNAME,
		'poses':[]
	}
	}

def conn():
	db = getattr(g, '_database', None)
	if db is None:
		db = g._database = sqlite3.connect(app.config['DATABASE'])
		db.execute('PRAGMA foreign_keys = ON')
		cursor = db.cursor()

@app.teardown_appcontext
def close_db(exception):
	db = getattr(g, '_database', None)
	if db is not None:
		db.close()

cred = credentials.Certificate(cred_file)
firebase_admin.initialize_app(cred)
db = firestore.client()

Storage = storage.Client.from_service_account_json(cred_file)

def get_firestore_db():
    return db

def is_data_unique(data,collection):
    query = collection.where("data", "==", data).limit(1).get()
    return len(query) == 0

def delete_document(collection_name, document_id):
    try:
        collection_ref = db.collection(collection_name)
        document_ref = collection_ref.document(document_id)
        document_ref.delete()
        return True
    except Exception as error:
        print(error)
        return False
    
app.config['ADMINS_REF'] = db.collection('admins')



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

def blocked(func):
	@wraps(func)
	def decorated_function(*args, **kwargs):
		if session['ADMIN']['status'] != 'active':
			if request.method == 'GET':
				return redirect(url_for('login'))
			elif request.method in ['POST', 'DELETE', 'PUT', 'PATCH']:
				return jsonify({'msg': 'Account blocked'}), 403
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

def check_values(values:list):
	for value in values:
		if value is None or not value or len(value) < 1:
			return False
	else:return True

def get_profile(host,account_id,token):
	try:
		url = f'{host}/account/{account_id}'
		headers = {
				'content-type':'application/json',
				'authorization': f'Bearer {token}'}
		data = httpx.get(url,headers=headers)
		if data.status_code > 299:return False,data.text
		return True,data.json()
	except Exception as error:
		return False,error
	
def get_stats(host,account_id,token):
	try:
		url = f'{host}/account/{account_id}/stats'
		headers = {
				'content-type':'application/json',
				'authorization': f'Bearer {token}'}
		data = httpx.get(url,headers=headers)
		if data.status_code > 299:return False,data.text
		return True,data.json()
	except Exception as error:
		return False,error





