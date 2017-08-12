# encoding: utf-8
import os
from airtable import airtable
from eventbrite import Eventbrite

EVENTBRITE_API_SECRET = os.getenv('EVENTBRITE_API_SECRET')
AIRTABLE_BASE_ID = os.getenv('EVENT_AIRTABLE_BASE_ID')
AIRTABLE_API_KEY = os.getenv('EVENT_AIRTABLE_API_KEY')
AIRTABLE_EVENTS_TABLE_ID = '🗓 Events'
AIRTABLE_EVENTS_VIEW_ID = 'viwnHWHuNNn9PEfrR'
AIRTABLE_CONTACTS_TABLE_ID = '🗃 Community'
AIRTABLE_TICKETS_TABLE_ID = '🎟 Tickets'

print('Get events from Airtable')
airtable_client = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)

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
      airtable_record = airtable_current_record
  else:
    print('Need to create {}'.format(airtable_id))
    airtable_record = airtable_client.create(airtable_id, new_params)
  return airtable_record

airtable_events = airtable_client.get(
    AIRTABLE_EVENTS_TABLE_ID, view=AIRTABLE_EVENTS_VIEW_ID
).get('records')
airtable_event_key_by_evenbrite_id = {
    airtable_event.get('fields').get('Eventbrite Id'): str(airtable_event.get('id'))
    for airtable_event in airtable_events
}
airtable_event = next(reversed(airtable_events))

print('Get emails from our community contacts in Airtable')
airtable_contacts = airtable_client.iterate(AIRTABLE_CONTACTS_TABLE_ID)
airtable_contact_by_email = {
  airtable_contact.get('fields').get('Email'): airtable_contact
  for airtable_contact in airtable_contacts
}

# TODO(florian): get only tickets of currently processed event?
print('Get tickets already copied to Airtable')
airtable_tickets = airtable_client.iterate(AIRTABLE_TICKETS_TABLE_ID)
airtable_ticket_by_ticket_id = {
  airtable_ticket.get('fields').get('Ticket Id'): airtable_ticket
  for airtable_ticket in airtable_tickets
}

def import_all_attendees_for_airtable_event(airtable_event):
  eventbrite_id = airtable_event.get('fields').get('Eventbrite Id')

  n = 0
  for eventbrite_attendee in get_eventbrite_attendees(eventbrite_id):
    n = n + 1
    ticket_id = eventbrite_attendee.get('id')

    eventbrite_contact = eventbrite_attendee.get('profile')
    email = eventbrite_contact.get('email')
    print("{}: {}".format(n, email))

    eventbrite_contact_params = {
      'Name': eventbrite_contact.get('name').title(),
      'Email': email,
      'Age': eventbrite_contact.get('age')
    }
    current_airtable_contact = airtable_contact_by_email.get(email)
    airtable_contact = create_or_update_on_airtable(AIRTABLE_CONTACTS_TABLE_ID, current_airtable_contact, eventbrite_contact_params)
    # Need to update the cache of contacts as multiple orders can link to the same contact
    # and will need a fresh version of it.
    airtable_contact_by_email[airtable_contact.get('fields').get('Email')] = airtable_contact
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
      '🗓 Event': [
          airtable_event_key_by_evenbrite_id[eventbrite_attendee.get('event_id')],
      ],
    }
    current_airtable_ticket = airtable_ticket_by_ticket_id.get(ticket_id)
    airtable_ticket = create_or_update_on_airtable(AIRTABLE_TICKETS_TABLE_ID, current_airtable_ticket, eventbrite_ticket_params)

eventbrite = Eventbrite(EVENTBRITE_API_SECRET)

def get_eventbrite_attendees(eventbrite_id):
  #  Eventbrite APU returns:
  #  "pagination": {
  #     "object_count": 430,
  #     "page_number": 1,
  #     "page_size": 50,
  #     "page_count": 7,
  #     "continuation": "eyJwYWdlIjogMn0",
  #     "has_more_items": true
  # },
  print('Get attendees from Eventbrite')
  continuation = ''
  while True:
      response = eventbrite.get('/events/{}/attendees?continuation={}'.format(eventbrite_id, continuation))
      for record in response.get('attendees'):
          yield record
      continuation = response['pagination'].get('continuation')
      if not continuation:
          break

for airtable_event in airtable_events:
  import_all_attendees_for_airtable_event(airtable_event)
