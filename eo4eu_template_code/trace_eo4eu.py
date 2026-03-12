from eo4eu_api_utils import Client
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result
from pathlib import Path
from datetime import datetime
import base64
import re
import time

def update_date(script: str):
    pattern = r'date = "\d{8}"'
    replacement = f'date = "{datetime.now().strftime("%Y%m%d")}"'
    script = re.sub(pattern, replacement, script)
    return script

def is_none(value):
    return value is None

@retry(
    retry=retry_if_result(is_none), 
    wait=wait_fixed(2),           
    stop=stop_after_attempt(10)   
)
def list_s3_bucket(client:Client, workflow_id):
    return client.list_s3_bucket(workflow_id)

@retry(
    retry=retry_if_result(is_none), 
    wait=wait_fixed(2),
    stop=stop_after_attempt(10)
)
def get_workflow_status(client:Client, workflow_id):
    try:
        response = client.get_workflow_info(workflow_id)
        return response['status']
    except:
        return None

@retry(
    wait=wait_fixed(2),
    stop=stop_after_attempt(10),                        
    reraise=True                                       
)
def connect_to_client(url, username, password):
    return Client(url, username, password)

# ------------------------------------------------------------------

url = 'https://umm-api.apps.eo4eu.eu'
username = 'apapakot'
password = 'Trace@2026'
workflow_id = "1c762b47-b804-40cc-957f-08f40be9c7da"

client = connect_to_client(url, username, password)
print("Connected to EO4EU API.")

pl = Path('pl.py').read_text(encoding='utf-8')
sfc = Path('sfc.py').read_text(encoding='utf-8')

updated_pl = update_date(pl)
updated_sfc = update_date(sfc)

scripts = [updated_pl, updated_sfc]
encoded_scripts = []
for script in scripts:
    encoded_scripts.append(base64.b64encode(script.encode("ascii")).decode("ascii"))
encoded_metadata = " "

data = {
    "query": encoded_scripts,
    "meta": encoded_metadata
}
client.workflow_update(workflow_id, data) 
client.workflow_start(workflow_id)
print("Workflow updated and started.")

while True:
    status = get_workflow_status(client, workflow_id)
    if status != 'COMPLETED':
        print(f"Workflow status: {status}. Please wait...")
        time.sleep(10)
    else:
        break
    
print("Listing S3 bucket contents:")
content = list_s3_bucket(client, workflow_id)

print(content)