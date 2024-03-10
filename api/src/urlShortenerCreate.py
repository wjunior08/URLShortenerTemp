import boto3
from boto3.dynamodb.types import TypeDeserializer
import json
import base64
import time
import os

dynamo = boto3.client('dynamodb')
ssm = boto3.client('ssm')

parameterName = os.environ['SSM_SHORTURL_TABLE_PARAMETER_NAME']
shortURLTableName = ssm.get_parameter(Name=parameterName)["Parameter"]["Value"]

def ddb_deserialize(r, type_deserializer = TypeDeserializer()):
    return type_deserializer.deserialize({"M": r})

def lambda_handler(event, context):
    '''Demonstrates a simple HTTP endpoint using API Gateway. You have full
    access to the request and response payload, including headers and
    status code.

    To scan a DynamoDB table, make a GET request with the TableName as a
    query string parameter. To put, update, or delete an item, make a POST,
    PUT, or DELETE request respectively, passing in the payload to the
    DynamoDB API as a JSON body.
    '''
    print("Received event: " + json.dumps(event))

    operation = event['httpMethod']
    
    if operation != 'POST':
        print("ERROR: operation "+operation+" on the POST function")
        return {
                    "isBase64Encoded": False,
                    "statusCode": 405,
                    "body": "http method not supported",
                }
    
    if "queryStringParameters" not in event or "fullURL" not in event["queryStringParameters"]:
        return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": "fullURL parameter is mandatory",
            }
    
    fullURL = event["queryStringParameters"]["fullURL"]
    auxNum = int(time.time())%10000000
    shortedURL = base64.urlsafe_b64encode(auxNum.to_bytes(3)).decode()
    
    try:
         result = dynamo.put_item(TableName = shortURLTableName,  Item={'shortedURL': {'S': shortedURL}, 'fullURL': {'S': fullURL}},)
         result = result["ResponseMetadata"]["HTTPStatusCode"]
    except Exception as e:
        print(e)
        return {
                "isBase64Encoded": False,
                "statusCode": 500,
                "headers": { "Content-Type": "application/json"},
                "body": "Server error"
                
            }
        
    
    if result == 200:
        body = {"shortedURL": shortedURL, "fullURL": fullURL}
        return  {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": { "Content-Type": "application/json"},
                "body": json.dumps(body)
        }
        
    return {
                "isBase64Encoded": False,
                "statusCode": 500,
                "headers": { "Content-Type": "application/json"},
                "body": "Server error"
                
            }
    