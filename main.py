# encoding: utf-8
import os
from airtable import airtable
from eventbrite import Eventbrite

EVENTBRITE_API_SECRET = os.getenv('EVENTBRITE_API_SECRET')
AIRTABLE_BASE_ID = os.getenv('EVENT_AIRTABLE_BASE_ID')
AIRTABLE_API_KEY = os.getenv('EVENT_AIRTABLE_API_KEY')
AIRTABLE_EVENTS_TABLE_ID = 'tblrq7mgDr3bH5P24'
AIRTABLE_EVENTS_VIEW_ID = 'viwnHWHuNNn9PEfrR'
AIRTABLE_CONTACTS_TABLE_ID = 'tbloEdq8Zw8GQ6l9R'
AIRTABLE_TICKETS_TABLE_ID = 'tblwjy7s3eeh8DWtT'

print('Get events from Airtable')
airtable_client = airtable.Airtable(AIRTABLE_BASE_ID, AIRTABLE_API_KEY)
airtable_events = airtable_client.get(
    AIRTABLE_EVENTS_TABLE_ID, view=AIRTABLE_EVENTS_VIEW_ID
).get('records')
airtable_event_key_by_evenbrite_id = {
    airtable_event.get('fields').get('Eventbrite Id'): str(airtable_event.get('id'))
    for airtable_event in airtable_events
}
airtable_last_event = next(reversed(airtable_events))
last_event_eventbrite_id = airtable_last_event.get('fields').get('Eventbrite Id')

print('Get emails from our community contacts in Airtable')
airtable_contacts = airtable_client.iterate(AIRTABLE_CONTACTS_TABLE_ID)
def a(b):
  print(b.get('fields').get('Email'))
  return ''

airtable_contact_by_email = {
  # 'a': airtable_contact
  airtable_contact.get('fields').get('Email'): airtable_contact
  for airtable_contact in airtable_contacts
}

print('Get tickets already copied to Airtable')
airtable_tickets = airtable_client.get(AIRTABLE_TICKETS_TABLE_ID).get('records')
airtable_ticket_by_ticket_id = {
  airtable_ticket.get('fields').get('Ticket Id'): airtable_ticket
  for airtable_ticket in airtable_tickets
}

print('Get attendees from Eventbrite')
eventbrite = Eventbrite(EVENTBRITE_API_SECRET)
eventbrite_last_event_attendees= eventbrite.get(
  '/events/{}/attendees/'.format(last_event_eventbrite_id)
)

def _create_or_update_on_airtable(airtable_id, airtable_current_record, new_params):
  if airtable_current_record:
    airtable_current_params = {
      key: airtable_current_record.get('fields').get(key) for key, value in new_params.items()
    }
    if new_params != airtable_current_params:
      print('Need to update')
      airtable_record = airtable_client.update(airtable_id, str(airtable_current_record.get('id')), new_params)
    else:
      # print('{} is up to date'.format(airtable_current_record.get('id')))
      airtable_record = airtable_current_record
  else:
    print('Need to create')
    airtable_record = airtable_client.create(airtable_id, new_params)
  return airtable_record

n = 0
for eventbrite_attendee in eventbrite_last_event_attendees.get('attendees'):
  n = n + 1
  ticket_id = int(eventbrite_attendee.get('id'))

  eventbrite_contact = eventbrite_attendee.get('profile')
  email = eventbrite_contact.get('email')
  print("{}: {}".format(n, email))

  eventbrite_contact_params = {
    'Name': eventbrite_contact.get('name').title(),
    'Email': email,
    'Age': eventbrite_contact.get('age')
  }
  current_airtable_contact = airtable_contact_by_email.get(email)
  airtable_contact = _create_or_update_on_airtable(AIRTABLE_CONTACTS_TABLE_ID, current_airtable_contact, eventbrite_contact_params)
  # Need to update the cache of contacts as multiple orders can link to the same contact
  # and will need a fresh version of it.
  airtable_contact_by_email[airtable_contact.get('fields').get('Email')] = airtable_contact

  eventbrite_ticket_params = {
    'Ticket Id': ticket_id,
    'Order Id': int(eventbrite_attendee.get('order_id')),
    '🗃 Contact': [airtable_contact.get('id')],
    'Status': eventbrite_attendee.get('status'),
    'Type': eventbrite_attendee.get('ticket_class_name'),
    '🗓 Event': [
        airtable_event_key_by_evenbrite_id[int(eventbrite_attendee.get('event_id'))],
     ],
     'Checked In?': True if eventbrite_attendee.get('checked_in') else None,
  }
  current_airtable_ticket = airtable_ticket_by_ticket_id.get(ticket_id)
  airtable_ticket = _create_or_update_on_airtable(AIRTABLE_TICKETS_TABLE_ID, current_airtable_ticket, eventbrite_ticket_params)
