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

    operation = event['httpMethod']

    if operation != 'GET':
        print("ERROR: operation "+operation+" on the GET function")
        return {
                        "isBase64Encoded": False,
                        "statusCode": 405,
                        "body": json.dumps({"message": "http method not supported"}),
                    }
            
    if "queryStringParameters" not in event or "shortKey" not in event["queryStringParameters"]:
        print("Shorte: shortedURL no present on request")
        return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": json.dumps({"message": "shortKey parameter is mandatory"}),
            }
    
    shortKey = event["queryStringParameters"]["shortKey"]
    body = ""
    
    try:
        result = dynamo.query(TableName = shortURLTableName, ExpressionAttributeValues={':shortKey': {'S': shortKey},}, KeyConditionExpression = 'shortKey = :shortKey')
    except Exception as e:
        print(e)
        return {
                "isBase64Encoded": False,
                "statusCode": 500,
                "headers": { "Content-Type": "application/json"},
                "body": json.dumps({"message": "Server error"})
                
            }
        
    
    if result["Count"] > 0 : 
        body = ddb_deserialize(result["Items"][0])
        return  {
                "isBase64Encoded": False,
                "statusCode": 200,
                "headers": { "Content-Type": "application/json"},
                "body": json.dumps(body)
                
            }
    else: 
        return {
                "isBase64Encoded": False,
                "statusCode": 404,
                "headers": { "Content-Type": "application/json"},
                "body": json.dumps({"message": "shortKey not found"})
                
            }
