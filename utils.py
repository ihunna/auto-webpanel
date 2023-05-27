from configs import proxy_file,datetime,timezone,random,string

def load_proxies():
    with open(proxy_file,'r') as pro_file:
        proxies = []
        for proxy in pro_file:
            proxy = proxy.replace("\n","").split(":")
            proxy = f"{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"
            proxies.append({
                "http://":f"http://{proxy}",
                "https://":f"http://{proxy}"
            })
    return proxies

def generate_sensor_data(type="password"):
    if type == "password":
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    elif type == "random_string":
        return  ''.join(random.choices('_' + string.digits + string.ascii_letters + '_', k=30))
    
    elif type == "random_numbers":
        return ''.join(random.choices(string.digits + string.digits, k=128))

def time_diff(old_time):
    old_time = datetime.fromisoformat(old_time)
    time_difference = datetime.now(timezone.utc) - old_time
    return abs(time_difference.total_seconds() / 3600)
    