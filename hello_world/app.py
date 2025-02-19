import os
import json
import requests
import boto3
from cloudflare import Cloudflare

def response(status_code, message):
    return {
        "statusCode": status_code,
        "body": json.dumps({
            "message": message
        }),
    }

def lambda_handler(event, context):
    
    STATUS_CODE_OK = 200
    STATUS_CODE_ERROR = 500
    STATUS_CODE = STATUS_CODE_OK
    MESSAGE = ""

    # ローカル開発時は環境変数から直接取得
    CLOUDFLARE_API = "https://api.cloudflare.com/client/v4/"

    
     # --- POSTでJSONを受け取り、IPを取得する処理を追加 ---
    print("DEBUG: event の内容:")
    print(json.dumps(event, indent=2, ensure_ascii=False))
    if event.get("body"):
        try:
            data = json.loads(event["body"])
            ip = data.get("ip")
            if not ip:
                raise ValueError("JSON内に'ip'が存在しません")
        except Exception as e:
            print("JSONパースエラー:", e)
            return response(STATUS_CODE_ERROR, "JSONパースエラー: " + str(e))
    else:
        return response(STATUS_CODE_ERROR, "JSONが存在しません")

    
    # ローカル開発時は環境変数から直接取得
    # デプロイ環境ではSSMパラメータストアから取得
    if 'CLOUDFLARE_API_TOKEN' in os.environ:
        api_token = os.environ['CLOUDFLARE_API_TOKEN']
        zone_id = os.environ['CLOUDFLARE_ZONE_ID']
        record_name = os.environ['CLOUDFLARE_RECORD_NAME']
    else:
        ssm = boto3.client('ssm')
        api_token = ssm.get_parameter(Name='/cloudflare-ddns-awssam/cloudflare-api-token', WithDecryption=True)['Parameter']['Value']
        zone_id = ssm.get_parameter(Name='/cloudflare-ddns-awssam/cloudflare-zone-id', WithDecryption=True)['Parameter']['Value']
        record_name = ssm.get_parameter(Name='/cloudflare-ddns-awssam/cloudflare-record-name', WithDecryption=True)['Parameter']['Value']
    
    
    client = Cloudflare(api_token=api_token)
    records = client.dns.records.list(zone_id=zone_id, name=record_name, type="A").result

    if len(records) == 0:
        MESSAGE = "DNSレコードが見つかりませんでした"
        STATUS_CODE = STATUS_CODE_ERROR

        return response(STATUS_CODE, MESSAGE)
    

    record = records[0]
    record_id = record.id

   
    # --- DNSレコード更新 ---
    client.dns.records.update(zone_id=zone_id, dns_record_id=record_id, content=ip, name=record_name, type='A')

    
    return {
        "statusCode": STATUS_CODE,
        "body": json.dumps({
            "message": MESSAGE,
            "ip": ip
        }),
    }
