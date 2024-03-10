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


    operation = event['httpMethod']

    if operation != 'GET':
        print("ERROR: operation "+operation+" on the GET function")
        return {
                        "isBase64Encoded": False,
                        "statusCode": 405,
                        "body": "http method not supported",
                    }
            
    if "queryStringParameters" not in event or "shortedURL" not in event["queryStringParameters"]:
        print("Shorte: shortedURL no present on request")
        return {
                "isBase64Encoded": False,
                "statusCode": 400,
                "body": "shortedURL parameter is mandatory",
            }
    
    shortedURL = event["queryStringParameters"]["shortedURL"]
    body = ""
    
    try:
        result = dynamo.query(TableName = shortURLTableName, ExpressionAttributeValues={':shortedURL': {'S': shortedURL},}, KeyConditionExpression = 'shortedURL = :shortedURL')
        body = ddb_deserialize(result["Items"][0])
    except Exception as e:
        print(e)
        return {
                "isBase64Encoded": False,
                "statusCode": 500,
                "headers": { "Content-Type": "application/json"},
                "body": "Server error"
                
            }
        
    
    if result["Count"] > 0 : 
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
                "body": "ShortedURL not found"
                
            }
