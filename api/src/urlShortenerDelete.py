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

def deleteKeyOnKVS(shortKey):
    describe = keyvaluestore.describe_key_value_store(KvsARN=shortURLKeyValueARN)
    etag = describe["ETag"]
    keyvaluestore.delete_key(KvsARN=shortURLKeyValueARN, Key=shortKey, IfMatch=etag)
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
        
    if "queryStringParameters" not in event or "shortKey" not in event["queryStringParameters"]:
        return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps({"message": "shortedURL parameter is mandatory"}),
            }
    shortKey = event["queryStringParameters"]["shortedURL"]
   
    
    try:
        result = dynamo.delete_item(TableName = shortURLTableName,  Key={'shortKey': {'S': shortKey}}) 
        result = result["ResponseMetadata"]["HTTPStatusCode"]
        if(useKVS): 
           deleteKeyOnKVS(shortKey)
    except Exception as e:
        print(e)
    if result == 200:
        body = json.dumps({"deletedKey": shortKey})
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
                "body": json.dumps({"message": "Server error"})
                
            }

        