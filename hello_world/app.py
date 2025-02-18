import os
import json
import requests
import boto3


def lambda_handler(event, context):

    CLOUDFLARE_API = "https://api.cloudflare.com/client/v4/"

    # デバッグ用：環境変数の値を確認
    print("Environment variables:")
    print(f"CLOUDFLARE_API_TOKEN: {os.environ.get('CLOUDFLARE_API_TOKEN', 'Not set')}")
    print(f"CLOUDFLARE_ZONE_ID: {os.environ.get('CLOUDFLARE_ZONE_ID', 'Not set')}")

    
    # ローカル開発時は環境変数から直接取得
    # デプロイ環境ではSSMパラメータストアから取得
    if 'CLOUDFLARE_API_TOKEN' in os.environ:
        api_token = os.environ['CLOUDFLARE_API_TOKEN']
        zone_id = os.environ['CLOUDFLARE_ZONE_ID']
    else:
        ssm = boto3.client('ssm')
        api_token = ssm.get_parameter(Name='/cloudflare/api-token', WithDecryption=True)['Parameter']['Value']
        zone_id = ssm.get_parameter(Name='/cloudflare/zone-id', WithDecryption=True)['Parameter']['Value']

    try:
        record_info = requests.get(
            f"{CLOUDFLARE_API}/zones/{zone_id}/dns_records",
            headers={
                "Authorization": f"Bearer {api_token}",
                "Content-Type": "application/json"
            },
            params={
                "name": "test.example.com",
                "type": "A"
            }
        )
        print(record_info.text)
    except requests.RequestException as e:
        print(e)
        raise e

    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    try:
        ip = requests.get("http://checkip.amazonaws.com/")
        print(ip.text)
    except requests.RequestException as e:
        # Send some context about this error to Lambda Logs
        print(e)

        raise e

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
