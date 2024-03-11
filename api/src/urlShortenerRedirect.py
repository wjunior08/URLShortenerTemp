import boto3
import json
import os

dynamo = boto3.client('dynamodb')
ssm = boto3.client('ssm')

parameterName = os.environ['SSM_SHORTURL_TABLE_PARAMETER_NAME']
shortURLTableName = ssm.get_parameter(Name=parameterName)["Parameter"]["Value"]

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err.message if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    '''Demonstrates a simple HTTP endpoint using API Gateway. You have full
    access to the request and response payload, including headers and
    status code.

    To scan a DynamoDB table, make a GET request with the TableName as a
    query string parameter. To put, update, or delete an item, make a POST,
    PUT, or DELETE request respectively, passing in the payload to the
    DynamoDB API as a JSON body.
    '''
    #print("Received event: " + json.dumps(event))

    operation = event['httpMethod']

    match operation:
        case 'GET':
            try:
                shortKey = event["requestContext"]["path"].split("/")[-1]
                result = dynamo.query(TableName = shortURLTableName, ExpressionAttributeValues={':shortKey': {'S': shortKey},}, KeyConditionExpression = 'shortKey = :shortKey')
            except Exception as e:
                print(e)
                return {
                        "isBase64Encoded": False,
                        "statusCode": 500,
                        "headers": { "Content-Type": "application/json"},
                        "body": json.dumps({"message":"Server error"})
                        
                    }
            redirectURL = "https://www.mercadolivre.com.br/404"
            
            if result["Count"] > 0 : 
                redirectURL = result["Items"][0]["fullURL"]["S"]
            
            return  {
                    "isBase64Encoded": False,
                    "statusCode": 302,
                    "headers": { "Location": redirectURL}
                }
        case _:
            return {
                        "isBase64Encoded": False,
                        "statusCode": 500,
                    }