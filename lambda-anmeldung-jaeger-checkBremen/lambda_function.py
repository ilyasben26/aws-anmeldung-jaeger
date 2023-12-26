import json
import scrapeFunc
import boto3
import os
from datetime import datetime, timedelta

sns_client = boto3.client('sns')
ddb_client = boto3.client('dynamodb')
s3_client = boto3.client('s3')

SNS_TOPIC_ARN = "arn:aws:sns:eu-central-1:045122203331:topic-anmeldung-jaeger-bremen"
TABLE_NAME = "ddb-anmeldung-jaeger-lambda-cache"
LAST_MESSAGE_TIME_KEY = "LastMessageTime"
BUCKET_NAME = "anmeldung-jaeger.com"
OBJECT_KEY = "data.json"


MESSAGE_THROTTLE_MINUTES = 20
SEND_MESSAGE = False


data = {
    "Bremen": [
        {
            "location": "BürgerServiceCenter-Nord",
            "url_get_token": "https://termin.bremen.de/termine",
            "url_get": "https://termin.bremen.de/termine/select2?md=6",
            "url_get_post": "https://termin.bremen.de/termine/location?mdt=702&select_cnc=1&cnc-8626=0&cnc-8627=0&cnc-8628=0&cnc-8650=0&cnc-8852=0&cnc-8604=0&cnc-8629=0&cnc-8633=0&cnc-8619=0&cnc-8647=0&cnc-8813=0&cnc-8652=0&cnc-8862=0&cnc-8801=0&cnc-8800=0&cnc-8793=0&cnc-8637=0&cnc-8639=1&cnc-8605=0&cnc-8606=0&cnc-8607=0&cnc-8608=0&cnc-8609=0&cnc-8610=0&cnc-8611=0&cnc-8613=0&cnc-8845=0&cnc-8869=0&cnc-8649=0&cnc-8603=0&cnc-8616=0&cnc-8620=0&cnc-8621=0&cnc-8622=0&cnc-8623=0&cnc-8624=0&cnc-8648=0&cnc-8837=0&cnc-8632=0&cnc-8634=0&cnc-8612=0&cnc-8641=0&cnc-8642=0&cnc-8643=0&cnc-8644=0&cnc-8645=0&cnc-8601=0&cnc-8602=0&cnc-8617=0&cnc-8614=0&cnc-8618=0&cnc-8625=0&cnc-8653=0&cnc-8646=0",
            "url_post": "https://termin.bremen.de/termine/suggest",
            "post_payload": "loc=681&gps_lat=999&gps_long=999&select_location=B%C3%BCrgerServiceCenter-Nord+ausw%C3%A4hlen"
        },
        {
            "location": "BürgerServiceCenter-Mitte",
            "url_get_token": "https://termin.bremen.de/termine",
            "url_get": "https://termin.bremen.de/termine/select2?md=5",
            "url_get_post": "https://termin.bremen.de/termine/location?mdt=701&select_cnc=1&cnc-8580=0&cnc-8582=0&cnc-8583=0&cnc-8587=0&cnc-8597=0&cnc-8579=0&cnc-8596=0&cnc-8599=0&cnc-8600=0&cnc-8797=0&cnc-8790=0&cnc-8588=0&cnc-8591=1&cnc-8798=0&cnc-8573=0&cnc-8844=0&cnc-8867=0&cnc-8789=0&cnc-8575=0&cnc-8578=0&cnc-8590=0",
            "url_post": "https://termin.bremen.de/termine/suggest",
            "post_payload": "loc=680&gps_lat=999&gps_long=999&select_location=B%C3%BCrgerServiceCenter-Mitte+ausw%C3%A4hlen"
        },
        {
            "location": "BürgerServiceCenter-Stresemannstraße",
            "url_get_token": "https://termin.bremen.de/termine",
            "url_get": "https://termin.bremen.de/termine/select2?md=4",
            "url_get_post": "https://termin.bremen.de/termine/location?mdt=705&select_cnc=1&cnc-8665=0&cnc-8674=0&cnc-8675=0&cnc-8676=0&cnc-8690=0&cnc-8854=0&cnc-8678=0&cnc-8679=0&cnc-8673=0&cnc-8689=0&cnc-8691=0&cnc-8692=0&cnc-8863=0&cnc-8693=0&cnc-8688=0&cnc-8804=0&cnc-8792=0&cnc-8682=0&cnc-8684=1&cnc-8803=0&cnc-8664=0&cnc-8666=0&cnc-8667=0&cnc-8668=0&cnc-8669=0&cnc-8670=0&cnc-8671=0&cnc-8672=0&cnc-8846=0&cnc-8865=0&cnc-8791=0&cnc-8802=0",
            "url_post": "https://termin.bremen.de/termine/suggest",
            "post_payload": "loc=682&gps_lat=999&gps_long=999&select_location=B%C3%BCrgerServiceCenter-Stresemannstra%C3%9Fe++ausw%C3%A4hlen"
        }
    ]
}


def lambda_handler(event, context):
    bremen_list = data["Bremen"]
    
    #checking the portal for each location
    results = scrapeFunc.check_bremen(bremen_list)
    
    # writing the results to S3
    modify_s3_data_object(results)
    
        
    # sending a message if any of the locations have available appointments
    if any(item["status"] == "available" for item in results):
        
        print("DEBUG: Available appointments!")
        
        # Calculate the current time
        current_time = datetime.now()
        print(f"DEBUG: current_time={current_time}")
        
        if SEND_MESSAGE:
            # Check the DyanamoDB table for the last message timestamp
            last_message_time = get_last_message_time()

            # If more than the specified minutes have passed, publish a message to SNS

            if last_message_time is None or (current_time - last_message_time) >= timedelta(minutes=MESSAGE_THROTTLE_MINUTES):
                message = format_message(results) 
           
                send_sns_message(message)
                update_last_message_time(current_time)
            else: 
                print("DEBUG: SNS message throttled")
        else:
            print("DEBUG: SEND_MESSAGE is set to False")
        
    
    return results
    

def modify_s3_data_object(results_dict):
    try:
        # Convert the dictionary to JSON
        json_data = json.dumps(results_dict)

        # Upload the JSON data to S3
        s3_client.put_object(
                Bucket=BUCKET_NAME, 
                Key=OBJECT_KEY, 
                Body=json_data.encode('utf-8'),
                ContentType='application/json'
            )
        
        print(f"DEBUG: S3 object {OBJECT_KEY} modified")
    except Exception as e:
        print(f"ERROR: Error updating S3 object: {e}")
    


def send_sns_message(content):
    try:
        response = sns_client.publish(TopicArn=SNS_TOPIC_ARN, Message=content)
        print("DEBUG: SNS message sent")
    except Exception as e:
        print(f"ERROR: Error publishing to SNS: {e}")
        
def get_last_message_time():
    try:
        response = ddb_client.get_item(
                TableName=TABLE_NAME,
                Key={'Key': {'S': 'LastMessageTime'}}
            )
        if 'Item' in response:
            fetched_timestamp = datetime.fromisoformat(response['Item']['Value']['S'])
            print(f"DEBUG: Fetched LastMessageTime: {fetched_timestamp}")
            return fetched_timestamp
    except Exception as e:
        print(f"ERROR: Error getting last message time: {e}")
    
def update_last_message_time(current_time):
    try:
        ddb_client.put_item(
            TableName=TABLE_NAME,
            Item={
                'Key': {'S': 'LastMessageTime'},
                'Value': {'S': current_time.isoformat()}
            }
        )
        print(f"DEBUG: LastMessageTime updated: {current_time}")
    except Exception as e:
        print(f"ERROR: Error updating last message time: {e}")

def format_message(results_dict):
    formatted_message = "There are free Anmeldung appointments available in the following locations:"
    for item in results_dict:
        if (item['status'] == 'available'):
            formatted_message += "\n"
            formatted_message += f"- {item['location']} at {item['datetime']}"
    return formatted_message
    
    