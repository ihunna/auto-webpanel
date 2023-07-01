from google.auth import default
from google.cloud import scheduler_v1
from os import environ
from app_configs import app
from app_utils import generate_uuid

class Scheduler:

    def __init__(self, location : str = "us-central1"):
        self.location = location
        _, self.project_id = default()
        self.client = scheduler_v1.CloudSchedulerClient()
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
        
    def create(self, user_id : str, model_id : str, account_id : str, schedule : str):
        job_name = generate_uuid(user_id, model_id, account_id)
        return self.client.create_job(request={
            "parent": self.parent,
            "job": {
                "name": self.client.job_path(self.project_id, self.location, job_name),
                "http_target": {
                    "uri": f"{app.config['BADOO_HOSTNAME']}/user/{user_id}/model/{model_id}/account/{account_id}/swipe",
                    "headers": {"key":app.config['BADOO_WORKER_KEY']},
                    "http_method": "POST"
                },
                "schedule": schedule,
                "time_zone": "UTC",
                "state": scheduler_v1.Job.State.DISABLED 
            }
        }).name
    
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
