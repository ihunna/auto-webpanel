from PIL import Image
import io,httpx
from uuid import uuid5, UUID


def sublist(lst : list, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

def identify_image_format(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return image.format
    except Exception as e:
        print(e)
        print("Error identifying image format:", str(e))
        return None
    
def generate_uuid(*values):
    SEED = UUID("87a5a26d-39fc-497c-8007-e4cf083b7a19")
    return str(uuid5(SEED, ''.join(values))).replace('-', '')


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
        
def write_log(file,log):
     with open(file,'w+',encoding='utf-8') as f:
          f.write(log)
	