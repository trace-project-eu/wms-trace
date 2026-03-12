from polytope.api import Client
import os

client = Client(address='polytope.lumi.apps.dte.destination-earth.eu', 
                    user_email= os.environ['DESTINY_USER_EMAIL'], 
                    user_key= os.environ['DESTINY_API_KEY']
                    )

# Optionally revoke previous requests
client.revoke('all')

# setup the request

date = "20260227"
param = "130/131/132/129"
levtype = "pl"
time = "0000/1800"
levelist = "500"
resolution = "standard"
points = [[38.5, 23], [37, 24.5]]

request = {
    "activity": "ScenarioMIP",
    "experiment": "SSP3-7.0",
    "class": "d1",
    "dataset": "climate-dt",
    "date": date,
    "expver": "0001",
    "generation": "1",
    "levtype": levtype,
    "model": "IFS-NEMO",
    'param': param,
    "realization": "1",
    "resolution": resolution,
    "stream": "clte",
    "time": time,
    "levelist": levelist,
    "type": "fc",
    "feature": {
        "type": "boundingbox",
        "points": points,
    },
}

# The data will be saved in the current working directory
files = client.retrieve('destination-earth', request, output_file = f"ClimateDT_{levtype}_{date}.json")