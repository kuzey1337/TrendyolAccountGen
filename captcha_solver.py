import requests
import time

def solve_recaptcha(api_key, site_key, site_url):
    create_task_url = 'https://api.capsolver.com/createTask'
    task_payload = {
        'clientKey': api_key,
        'task': {
            'type': 'RecaptchaV2TaskProxyless',
            'websiteURL': site_url,
            'websiteKey': site_key
        }
    }
    
    try:
        response = requests.post(create_task_url, json=task_payload)
        if response.status_code == 200:
            task_id = response.json().get('taskId')
            return task_id
        else:
            raise Exception(f"Failed to create task: {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error creating task: {str(e)}")

def get_task_result(api_key, task_id):
    get_task_result_url = 'https://api.capsolver.com/getTaskResult'
    result_payload = {
        'clientKey': api_key,
        'taskId': task_id
    }

    try:
        while True:
            response = requests.post(get_task_result_url, json=result_payload)
            if response.status_code == 200:
                result = response.json()
                if result['status'] == 'ready':
                    return result['solution']['gRecaptchaResponse']
                elif result['status'] == 'processing':
                    time.sleep(5)
                else:
                    raise Exception(f"Task failed: {result.get('errorDescription')}")
            else:
                raise Exception(f"Failed to get task result: {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error getting task result: {str(e)}")