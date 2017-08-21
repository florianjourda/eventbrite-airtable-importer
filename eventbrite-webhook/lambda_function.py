# encoding: utf-8
print('Loading function')
import json
import os
import sys
# sys.path.append(os.path.join(os.path.dirname(__file__), ''))

from airtable import airtable
from eventbrite import Eventbrite

EVENTBRITE_API_SECRET = os.getenv('EVENTBRITE_API_SECRET')
AIRTABLE_BASE_ID = os.getenv('EVENT_AIRTABLE_BASE_ID')
AIRTABLE_API_KEY = os.getenv('EVENT_AIRTABLE_API_KEY')
AIRTABLE_EVENTS_TABLE_ID = '🗓 Events'
AIRTABLE_CONTACTS_TABLE_ID = '🗃 Community'
AIRTABLE_TICKETS_TABLE_ID = '🎟 Tickets'

airtable_client = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)
eventbrite = Eventbrite(EVENTBRITE_API_SECRET)

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

    eventbrite_attendee = None
    if body.get('config', {}).get('action') == 'attendee.updated':
      eventbrite_attendee = get_evenbrite_object(body)
      airtable_ticket = save_ticket_in_airtable(eventbrite_attendee)

      return {"statusCode": 200, \
          "headers": {"Content-Type": "application/json"}, \
          "body": json.dumps({
              'airtable_ticket': airtable_ticket,
          }, indent=2)}

    return {"statusCode": 404, \
    "headers": {"Content-Type": "application/json"}, \
    "body": json.dumps({
        'action_not_supported': body.get('config', {}).get('action'),
    }, indent=2)}

def get_evenbrite_object(body):
    api_url = body.get('api_url', '')
    response = eventbrite.get(api_url)
    print(response)
    return response

def save_ticket_in_airtable(eventbrite_attendee):
    ticket_id = eventbrite_attendee['id']
    eventbrite_contact = eventbrite_attendee['profile']
    email = eventbrite_contact['email'].lower()
    eventbrite_id = eventbrite_attendee['event_id']

    print('Get event from Airtable')
    airtable_event = get_airtable_event(eventbrite_id)
    print(airtable_event)

    print('Create or update Airtable contact')
    current_airtable_contact = get_airtable_contact(email)
    current_airtable_name = current_airtable_contact and current_airtable_contact.get('fields').get('Name')
    eventbrite_contact_params = {
      'Name': current_airtable_name or eventbrite_contact.get('name').title(),
      'Email': email,
      'Age': eventbrite_contact.get('age')
    }
    airtable_contact = create_or_update_on_airtable(AIRTABLE_CONTACTS_TABLE_ID, current_airtable_contact, eventbrite_contact_params)
    print(airtable_contact)

    print('Create or update Airtable ticket')
    current_airtable_ticket = get_airtable_ticket(ticket_id)
    eventbrite_ticket_params = {
      # Airtable add .000 at the end of dates so we do the same for the value from Eventbrite
      # in order to be able to compare correctly the dates from the two repositories.
      'Created At': eventbrite_attendee.get('created').replace("Z", ".000Z"),
      'Ticket Id': ticket_id,
      'Order Id': eventbrite_attendee.get('order_id'),
      '🗃 Contact': [airtable_contact.get('id')],
      'Status': eventbrite_attendee.get('status'),
      'Type': eventbrite_attendee.get('ticket_class_name'),
      'Affiliate': eventbrite_attendee.get('affiliate'),
      'Checked In?': True if eventbrite_attendee.get('checked_in') else None,
      '🗓 Event': [airtable_event.get('id')],
    }
    airtable_ticket = create_or_update_on_airtable(AIRTABLE_TICKETS_TABLE_ID, current_airtable_ticket, eventbrite_ticket_params)
    print(airtable_ticket)
    return airtable_ticket

def get_airtable_event(eventbrite_id):
  airtable_events = airtable_client.get(
      AIRTABLE_EVENTS_TABLE_ID,
      filter_by_formula='{{Eventbrite Id}}="{}"'.format(eventbrite_id),
      fields=['Eventbrite Id'],
  ).get('records')
  if not airtable_events:
    print('Eventbrite id {} not found in Airtable Events table'.format(eventbrite_id))
    return None
  else:
    return airtable_events[0]

def get_airtable_contact(email):
  airtable_contacts = airtable_client.get(
      AIRTABLE_CONTACTS_TABLE_ID,
      filter_by_formula='{{Email}}="{}"'.format(email),
      fields=['Name', 'Email', 'Age'],
  ).get('records')
  if not airtable_contacts:
    print('Email {} not found in Airtable Community table'.format(email))
    return None
  else:
    return airtable_contacts[0]

def get_airtable_ticket(ticket_id):
  airtable_tickets = airtable_client.get(
      AIRTABLE_TICKETS_TABLE_ID,
      filter_by_formula='{{Ticket Id}}="{}"'.format(ticket_id),
  ).get('records')
  if not airtable_tickets:
    print('Ticket Id {} not found in Airtable Ticket table'.format(ticket_id))
    return None
  else:
    return airtable_tickets[0]

def create_or_update_on_airtable(airtable_id, airtable_current_record, new_params):
  if airtable_current_record:
    airtable_current_params = {
      key: airtable_current_record.get('fields').get(key) for key, value in new_params.items()
    }
    if new_params != airtable_current_params:
      print('Need to update {}'.format(airtable_id))
      airtable_record = airtable_client.update(airtable_id, str(airtable_current_record.get('id')), new_params)
    else:
      # print('{} is up to date'.format(airtable_current_record.get('id')))
      print('Already uptodate')
      airtable_record = airtable_current_record
  else:
    print('Need to create {}'.format(airtable_id))
    airtable_record = airtable_client.create(airtable_id, new_params)
  return airtable_record

