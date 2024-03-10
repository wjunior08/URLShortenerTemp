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

def deleteKeyOnKVS(shortedURL, fullURL):
    describe = keyvaluestore.describe_key_value_store(KvsARN=shortURLKeyValueARN)
    etag = describe["ETag"]
    keyvaluestore.delete_key(KvsARN=shortURLKeyValueARN, Key=shortedURL, IfMatch=etag)
    return True

def lambda_handler(event, context):

    operation = event['httpMethod']

    if operation != 'DELETE':
        print("ERROR: operation "+operation+" on the delete function")
        return {
                    "isBase64Encoded": False,
                    "statusCode": 405,
                    "body": "http method not supported",
                }
        
    if "queryStringParameters" not in event or "shortedURL" not in event["queryStringParameters"]:
        return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": "shortedURL parameter is mandatory",
            }
    shortedURL = event["queryStringParameters"]["shortedURL"]
   
    
    try:
        result = dynamo.delete_item(TableName = shortURLTableName,  Key={'shortedURL': {'S': shortedURL}}) 
        result = result["ResponseMetadata"]["HTTPStatusCode"]
        if(useKVS): 
            keyvaluestore.delete_key(Id=shortURLKeyValueId, Key=shortedURL)
    except Exception as e:
        print(e)
    if result == 200:
        body = shortedURL + " successfully deleted"
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

        