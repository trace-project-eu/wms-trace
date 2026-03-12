import base64
import time
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_result
from eo4eu_api_utils import Client
import requests
import os

# -------------------------
# Configuration
# -------------------------
EO4EU_URL = 'https://umm-api.apps.eo4eu.eu'
EO4EU_USERNAME = 'apapakot'
EO4EU_PASSWORD = 'Trace@2026'
WORKFLOW_ID = "f61488fb-9d1a-4bad-ad5b-dd2b1b95db88"


# -------------------------
# Tenacity Retry Helpers
# -------------------------
def is_none(value):
    return value is None


@retry(retry=retry_if_result(is_none), wait=wait_fixed(2), stop=stop_after_attempt(10))
def get_workflow_status(client: Client, workflow_id):
    try:
        response = client.get_workflow_info(workflow_id)
        return response.get('status')
    except:
        return None


@retry(wait=wait_fixed(2), stop=stop_after_attempt(10), reraise=True)
def connect_to_client(url, username, password):
    return Client(url, username, password)


# -------------------------
# Dynamic Script Generators
# -------------------------
def generate_polytope_script(levtype, param, points, levelist=None):
    """Generates the Polytope Python script dynamically with the current date."""
    # Always gets the current date in YYYYMMDD format
    current_date = datetime.now().strftime("%Y%m%d")

    script = f"""from polytope.api import Client
import os

client = Client(address='polytope.lumi.apps.dte.destination-earth.eu', 
                user_email=os.environ.get('DESTINY_USER_EMAIL'), 
                user_key=os.environ.get('DESTINY_API_KEY'))

client.revoke('all')

request = {{
    "activity": "ScenarioMIP",
    "experiment": "SSP3-7.0",
    "class": "d1",
    "dataset": "climate-dt",
    "date": "{current_date}",
    "expver": "0001",
    "generation": "1",
    "levtype": "{levtype}",
    "model": "IFS-NEMO",
    "param": "{param}",
    "realization": "1",
    "resolution": "standard",
    "stream": "clte",
    "time": "0000/1800",
    "type": "fc",
"""
    if levelist:
        script += f'    "levelist": "{levelist}",\n'

    script += f"""    "feature": {{
        "type": "boundingbox",
        "points": {points},
    }}
}}

files = client.retrieve('destination-earth', request, output_file="ClimateDT_{levtype}_{current_date}.json")
"""
    return script, current_date


def download_presigned_urls(bucket_contents):
    """
    Takes the output from list_s3_bucket and downloads the ClimateDT JSON files.
    """
    for item in bucket_contents:
        file_path = item.get('name', '')
        download_url = item.get('presignedUrl')

        # We only want to download the weather data files, skipping metainfo.json
        if "ClimateDT" in file_path and download_url:
            # Extract just the filename from the path (e.g., "ClimateDT_pl_20260312.json")
            filename = os.path.basename(file_path)

            print(f"⬇️ Downloading {filename}...")

            # Standard HTTP GET request using the requests library
            response = requests.get(download_url)

            if response.status_code == 200:
                with open(filename, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Successfully saved {filename}")
            else:
                print(f"❌ Failed to download {filename}. HTTP Status: {response.status_code}")


# -------------------------
# Main Execution Function
# -------------------------
def fetch_current_eo4eu_data(points=[[38.5, 23], [37, 24.5]]):
    """
    Executes the EO4EU workflow to fetch surface and pressure level data.
    Returns the date string used, which helps locate the generated output files.
    """
    client = connect_to_client(EO4EU_URL, EO4EU_USERNAME, EO4EU_PASSWORD)
    print("✅ Connected to EO4EU API.")

    # 1. Generate scripts dynamically
    sfc_script, current_date = generate_polytope_script(
        levtype="sfc",
        param="144/141/228/260048",
        points=points
    )

    pl_script, _ = generate_polytope_script(
        levtype="pl",
        param="130/131/132/129",
        points=points,
        levelist="500"
    )

    # 2. Encode payloads
    encoded_scripts = [
        base64.b64encode(s.encode("ascii")).decode("ascii") for s in [pl_script, sfc_script]
    ]

    # 3. Update and Start Workflow
    client.workflow_update(WORKFLOW_ID, {"query": encoded_scripts, "meta": " "})
    client.workflow_start(WORKFLOW_ID)
    print(f"🚀 Workflow started for date: {current_date}")

    # 4. Wait for completion
    while True:
        status = get_workflow_status(client, WORKFLOW_ID)
        if status == 'COMPLETED':
            print("✅ Workflow COMPLETED.")
            break
        elif status in ['FAILED', 'ERROR']:
            print(f"❌ Workflow failed with status: {status}")
            return None
        print(f"⏳ Workflow status: {status}. Sleeping 10s...")
        time.sleep(10)

    # 5. List and (Optionally) Download from S3
    print("\n📦 Listing S3 bucket contents:")
    content = client.list_s3_bucket(WORKFLOW_ID)
    print(content)

    # 6. Download the files using the standard requests library
    download_presigned_urls(content)

    return current_date


if __name__ == "__main__":
    # Test execution
    fetch_current_eo4eu_data()