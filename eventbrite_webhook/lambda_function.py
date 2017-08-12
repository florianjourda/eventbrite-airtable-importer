print('Loading function')
import json
from eventbrite import Eventbrite

# Receives this payload from Eventbrite:
# {
#   "api_url": "https://www.eventbriteapi.com/v3/events/36702403878/attendees/823010854/",
#   "config": {
#     "action": "attendee.updated",
#     "endpoint_url": "https://2vv4q857ml.execute-api.us-east-1.amazonaws.com/prod/import-eventbrite-attendees-to-airtable",
#     "user_id": "162648120486",
#     "webhook_id": "455733"
#   }
# }


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))
    body = json.loads(event.get('body', '{}'))
    res = '-'
    # res = json.dumps(event.get('config', {}), indent=2)
    if body.get('config', {}).get('action') == 'attendee.updated':
      res = 'Yay!'
    # maxPrime = int(event['queryStringParameters']['max'])

    return {"statusCode": 200, \
        "headers": {"Content-Type": "application/json"}, \
        "body": json.dumps({
            'body': body,
            'config': body.get('config', {}),
            'action': body.get('config', {}).get('action'),
            'res': res,
        }, indent=2)}
