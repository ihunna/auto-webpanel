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

        
def write_log(file,log):
     with open(file,'w+',encoding='utf-8') as f:
          f.write(log)

def create_edit_menu(data):
    edit_menus = ""
    for key, values in data.items():
        edit_menus += f'<div>'
        edit_menus += f'<label for="{key}">{key.capitalize()}: </label>'
        edit_menus += f'<select name="{key}" id="{key}">'
        for value in values:
            edit_menus += f'<option value="{value}">{value}</option>'
        edit_menus += '</select>'
        edit_menus += '</div>'
    return edit_menus

def share_daily_percent(day_specs:dict):
    daily_swipe_percent = []
    for day in day_specs:
        range_parts = day['day'].split("-")
        start_day = int(range_parts[0])
        end_day = int(range_parts[1])
        
        for i in range(start_day, end_day + 1):
            daily_swipe_percent.append({'day':i,'swipe_percent':day['swipe_percent']})
    return daily_swipe_percent
	