import requests,httpx,random,json,string,os,time,uuid
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from PIL import Image
from os import listdir
from os.path import isfile,abspath
from dotenv import load_dotenv


basedir = os.path.join(os.path.dirname(__file__))
env_path = os.path.join(basedir, '.env')
proxy_file = os.path.join(basedir, 'proxies.txt')
img_folder = os.path.join(basedir,'images')

from utils import load_proxies
proxies = load_proxies()

load_dotenv(env_path)
api_key = os.getenv('APIKEY')

bearer = {'bearer_token':'','expiration':'','ticks':638183993789653455}
