from google.auth import default
from google.cloud import scheduler_v1
from app_configs import cred, cred_file
from app_utils import generate_uuid
import json,uuid,random
from datetime import datetime, timedelta

class Scheduler:

    def __init__(self,location : str = "us-central1"):
        self.location = location
        self.project_id = 'atowebpanel'
        self.client = scheduler_v1.CloudSchedulerClient.from_service_account_file(cred_file)
        self.parent = f"projects/{self.project_id}/locations/{self.location}"

    def _update(self, job_path, state : scheduler_v1.Job.State = None):
        job = self.client.get_job(request={
            "name": job_path
        })
        if state is not None:
            job.state = state
        return self.client.update_job(request={
            "job": job
        })
        
    def create(self,cron_exp:list, url:str, payload:dict = {}):
        try:
            for day in cron_exp:
                job_name = generate_uuid(str(uuid.uuid4()))
                job_path = self.client.job_path(self.project_id, self.location, job_name)

                payload['job_path'] = job_path
                payload['daily_percent'] = day['daily_percent']
                payload['daily_percent']['session'] = day['session']
                body_bytes = json.dumps(payload).encode('utf-8')
                
                schedule = self.client.create_job(request={
                    "parent": self.parent,
                    "job": {
                        "name": job_path,
                        "http_target": {
                            "uri": url,
                            "headers": {'Content-Type': 'application/json'},
                            "http_method": "POST",
                            "body": body_bytes
                        },
                        "schedule": day['cron'].strip(),
                        "time_zone": "UTC",
                        "state": scheduler_v1.Job.State.ENABLED
                    }
                }).name

                if schedule is None or not schedule: return False, 'Schedule creation failed'

            return True, 'Schedule created successfully'
        except Exception as error:
            return False, error
    
    def delete(self, job_path : str):
        return self.client.delete_job(request={
            "name": job_path
        })
    
    def start(self, job_path : str):
        return self._update(job_path, state=scheduler_v1.Job.State.ENABLED)
    
    def stop(self, job_path : str):
        return self._update(job_path, state=scheduler_v1.Job.State.DISABLED)
    
    def run(self, job_path : str):
        return self.client.run_job(request={
            "name": job_path
        })
    
    def is_running(self, job_path):
        job = self.client.get_job(request={
            "name": job_path
        })
        return job.state == scheduler_v1.Job.State.ENABLED

    def generate_cron_expression(self,start_date, end_date, session_count=1, operation_duration=60,daily_percent:list=[]):
        res = []
        date_interval = end_date - start_date
        if date_interval.days <= 1:
            session_start_time = start_date
            for session in range(session_count):
                d_gap = random.randint(1,3)
                session_start_time_str = session_start_time.strftime('%M %H')
                res.append({
                    'day':1,
                    'cron':f'{session_start_time_str} {start_date.day} {start_date.month} *',
                    'daily_percent':daily_percent[0],
                    'session':session+1
                    }) 
                session_start_time += timedelta(minutes=(operation_duration + d_gap))
        else:
            date_range = end_date - start_date
            for i in range(date_range.days):
                current_date = start_date + timedelta(days=i)

                day = current_date.day
                month = current_date.month
                year = current_date.year

                session_start_time = start_date
                for session in range(session_count):
                    d_gap = random.randint(1,3)
                    session_start_time_str = session_start_time.strftime('%M %H')
                    res.append({
                        'day':i+1,
                        'cron':f'{session_start_time_str} {day} {month} *',
                        'daily_percent':daily_percent[i],
                        'session':session+1
                        }) 
                    session_start_time += timedelta(minutes=(operation_duration + d_gap))

        return res



    
    def get_date_format(self,date_string:str,date_format:str='%Y-%m-%dT%H:%M:%S'):
        date_object = datetime.strptime(date_string, date_format)
        year = date_object.year
        month = date_object.month
        day = date_object.day
        hour = date_object.hour
        minute = date_object.minute
        second = date_object.second

        return (year, month, day, hour, minute, second)