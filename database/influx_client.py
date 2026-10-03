# database/influx_client.py

from influxdb_client_3 import InfluxDBClient3

HOST = "https://us-east-1-1.aws.cloud2.influxdata.com"
TOKEN = "7nrflevA_ZN2YGy57rSJu2YxtyidVzsZQYDROoHZSQI6F2mIixMRVdKo2rxMrZIIB6hpOTmOVB5OKYwNkYcsWw=="
ORG = "Fish"

client = InfluxDBClient3(
    host=HOST,
    token=TOKEN,
    org=ORG,
    database="fishfarm"
)