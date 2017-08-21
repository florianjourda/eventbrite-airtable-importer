function processRequest(e) {
    if (xhr.readyState == 4 && xhr.status == 200) {
        var response = JSON.parse(xhr.responseText);
        console.log(response);
        fillForms(response.records);
    }
}

function fillForms(contacts) {
    document.getElementById('first_name').value='Daybreaker';
    document.getElementById('last_name').value='Paris';
    document.getElementById('email_address').value='paris@daybreaker.com';

    contacts.forEach(function(contact, index) {
         console.log(contact, index);
         var key = 'id_attendee_' + (index + 1);
         var name = contact.fields.Name;
         document.getElementById(key + '_first_name').value = name.split(' ')[0];
         document.getElementById(key + '_last_name').value = name.split(' ').slice(1).join(' ');
         document.getElementById(key + '_email_address').value=contact.fields.Email;
         document.querySelectorAll('.waiver_input').forEach(function(e) {e.checked='checked';});
    });
}

var xhr = new XMLHttpRequest();
xhr.open('GET', 'https://api.airtable.com/v0/appKUBXe1LZpfGAYB/%F0%9F%97%83%20Community?view=viw3MZnDzKSZmHAAo&fields[]=Email&fields[]=Name', true);
xhr.setRequestHeader('Authorization', 'Bearer XXXXXXXXXXX');
xhr.send();
xhr.onreadystatechange = processRequest;
