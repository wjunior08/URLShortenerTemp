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