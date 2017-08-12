import os
from airtable import airtable
from eventbrite import Eventbrite

EVENTBRITE_API_SECRET = os.getenv('EVENTBRITE_API_SECRET')
AIRTABLE_BASE_ID = os.getenv('EVENT_AIRTABLE_BASE_ID')
AIRTABLE_API_KEY = os.getenv('EVENT_AIRTABLE_API_KEY')
AIRTABLE_EVENTS_TABLE_ID = 'tblrq7mgDr3bH5P24'
AIRTABLE_EVENTS_VIEW_ID = 'viwnHWHuNNn9PEfrR'
AIRTABLE_ORDERS_TABLE_ID = 'tblwjy7s3eeh8DWtT'

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

print('Get tickets already copied to Airtable')
airtable_tickets = airtable_client.get(AIRTABLE_ORDERS_TABLE_ID).get('records')
airtable_ticket_by_order_id = {
  airtable_ticket.get('fields').get('Order Id'): airtable_ticket
  for airtable_ticket in airtable_tickets
}

print('Get attendees from Eventbrite')
eventbrite = Eventbrite(EVENTBRITE_API_SECRET)
eventbrite_last_event_orders = eventbrite.get(
  '/events/{}/attendees/'.format(last_event_eventbrite_id)
)
eventbrite_order = eventbrite_last_event_orders.get('attendees')[0]
eventbrite_profile = eventbrite_order.get('profile')
order_id = int(eventbrite_order.get('order_id'))

eventbrite_ticket_params = {
  'Order Id': order_id,
  'Name': eventbrite_profile.get('name'),
  'Email': eventbrite_profile.get('email'),
  'Status': eventbrite_order.get('status'),
  'Type': eventbrite_order.get('ticket_class_name'),
  'Event': [
      airtable_event_key_by_evenbrite_id[int(eventbrite_order.get('event_id'))].decode('utf-8'),
   ],
   'Checked In?': True if eventbrite_order.get('checked_in') else None,
}

airtable_ticket = airtable_ticket_by_order_id.get(order_id)

if airtable_ticket:
  airtable_ticket_params = {
    key: airtable_ticket.get('fields').get(key) for key, value in eventbrite_ticket_params.items()
  }
  # print(eventbrite_ticket_params)
  # print(airtable_ticket_params)
  if eventbrite_ticket_params != airtable_ticket_params:
    print('Need update')
    res = airtable_client.update(AIRTABLE_ORDERS_TABLE_ID, str(airtable_ticket.get('id')), eventbrite_ticket_params)
    print(res)
  else:
    print('No change')
else:
  res = airtable_client.create(AIRTABLE_ORDERS_TABLE_ID, eventbrite_ticket_params)
  print(res)
