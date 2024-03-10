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

parameterName = os.environ['SSM_SHORTURL_KEYVALUE_PARAMETER_ARN']
useKVS = False
if(parameterName != "False"):
    useKVS = True
    shortURLKeyValueARN = ssm.get_parameter(Name=parameterName)["Parameter"]["Value"]
    keyvaluestore = boto3.client('cloudfront-keyvaluestore')

def ddb_deserialize(r, type_deserializer = TypeDeserializer()):
    return type_deserializer.deserialize({"M": r})

def putKeyOnKVS(shortedURL, fullURL):
    describe = keyvaluestore.describe_key_value_store(KvsARN=shortURLKeyValueARN)
    etag = describe["ETag"]
    keyvaluestore.put_key(KvsARN=shortURLKeyValueARN, Key=shortedURL, Value=fullURL, IfMatch=etag)
    return True

def lambda_handler(event, context):

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
         if(useKVS):
            putKeyOnKVS(shortedURL, fullURL)
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
    