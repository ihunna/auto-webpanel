from configs import proxy_file,datetime,timezone,random,string


def get_proxies():
    proxies = []
    with open(proxy_file,"r") as f:
        for proxy in f.readlines():
            proxy = proxy.replace("\n","").split(":")
            ip = proxy[0]
            port = proxy[1]
            username = proxy[2]
            password = proxy[3] if len(proxy) > 3 else None
            if password is not None:
                proxy = {
                    "http://": f'http://{username}:{password}@{ip}:{port}',
                    "https://": f'http://{username}:{password}@{ip}:{port}'
                }
            else:
                 proxy = {
                    "http://": f'http://{username}:@{ip}:{port}',
                    "https://": f'http://{username}:@{ip}:{port}'
                }
                 
            proxies.append(proxy)

    return proxies

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
    