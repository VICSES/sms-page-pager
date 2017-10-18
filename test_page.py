import pytest
import page # My site

from twilio.request_validator import RequestValidator
from unittest.mock import call, patch
from moto import mock_dynamodb2
from moto.dynamodb2.models import dynamodb_backend2
import os

os.environ['STAGE'] = 'TEST'


@pytest.fixture
def app():
    app = page.app
    app.testing = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def mock_viper():
    with patch('page.Viper') as mock:
        instance = mock.return_value
        instance.send.return_value = False
        yield mock

@pytest.fixture
def dynamodb():
    with mock_dynamodb2():
        yield dynamodb_backend2

def get_dyn_name(table):
    return 'sms-page-TEST-'+table

@pytest.fixture
def contact_table(dynamodb):
    return dynamodb.create_table(get_dyn_name("contact"),schema=[
        {u'KeyType': u'HASH', u'AttributeName': u'phone_number'}
    ])

@pytest.fixture
def unit_table(dynamodb):
    return dynamodb.create_table(get_dyn_name("unit"),schema=[
        {u'KeyType': u'HASH', u'AttributeName': u'name'}
    ])

@pytest.fixture
def pagelog_table(dynamodb):
    return dynamodb.create_table(get_dyn_name("page_log"),schema=[
        {u'KeyType': u'HASH', u'AttributeName': u'unit'},
        {u'KeyType': u'RANGE', u'AttributeName': u'timestamp'},
    ])


# test_page tests the page() function in page.py
# It is accessed by the route /


# validate_twilio_request is a function decorator on page() that
# checks the X-TWILIO-SIGNATURE hash to ensure that
# the request originated from Twilio
# The hash algorithm is documented at https://www.twilio.com/docs/api/security
def test_twilio_check(client):
    token = "AABBCCDD"
    data = {
            'Body' : 'Twilio check body',
            'From' : '1234567890'
    }

    # Monkey patch the app's environment hash
    page.os.environ['TWILIO_AUTH_TOKEN'] = token

    validator = RequestValidator(token)
    sig = validator.compute_signature('http://localhost/', data)

    # TODO: Incoming number is +61...

    # Good request
    # Response will be an TWIML error response
    # Don't care, Twilio auth check passed
    good_headers = {'X-TWILIO-SIGNATURE' : sig}
    good = client.post('/', data=data, headers=good_headers)
    assert(good.status_code == 200)

    # Request missing headers
    missing = client.post('/', data=data, headers={})
    assert(missing.status_code == 403)

    # Request with bad header
    bad_headers = {'X-TWILIO-SIGNATURE' : 'RABBITHAT'}
    bad = client.post('/', data=data, headers=bad_headers)
    assert(bad.status_code == 403)

    # Request signature with bad url
    sig = validator.compute_signature('http://otherhost/', data)
    bad_url_headers = {'X-TWILIO-SIGNATURE' : sig}
    bad_url = client.post('/', data=data, headers=bad_url_headers)
    assert(bad_url.status_code == 403)

    # Request signature with bad data
    extra_data = data.copy()
    extra_data['flubble'] = 'wubble'
    sig = validator.compute_signature('http://localhost/', extra_data)
    bad_data_headers = {'X-TWILIO-SIGNATURE' : sig}
    bad_data = client.post('/', data=data, headers=bad_data_headers)
    assert(bad_data.status_code == 403)

    # Request signature with messed up token
    page.os.environ['TWILIO_AUTH_TOKEN'] = "I laugh at them because they're all the same"
    bad_token = client.post('/', data=data, headers=good_headers)
    assert(bad_token.status_code == 403)

def test_db_lookups(client, contact_table, unit_table, mock_viper):
    data = {
            'Body' : 'Twilio check body',
            'From' : '1234567890'
    }
    token = "AABBCCDD"
    page.os.environ['TWILIO_AUTH_TOKEN'] = token
    validator = RequestValidator(token)
    sig = validator.compute_signature('http://localhost/', data)
    headers = {'X-TWILIO-SIGNATURE' : sig}


    not_auth = client.post('/', data=data, headers=headers)
    assert(not_auth.status_code == 200)
    assert(b"You are not authorised to use this service" in not_auth.data)


    contact_table.put_item({
        'phone_number' : {'S' : '1234567890'},
        'unit'         : {'S' : 'TestData'},
        'name'         : {'S' : 'John Smith'},
        'member_id'    : {'N' :12345},
        'permissions'  : {'S' : '{}'}
    })

    not_unit = client.post('/', data=data, headers=headers)
    assert(not_unit.status_code == 200)
    assert(b"You are not authorised to use this service" not in not_unit.data)
    assert(b"Error retrieving unit details" in not_unit.data)
    assert(mock_viper.mock_calls == [])


    unit_table.put_item({
        'name' : {'S': 'TestData'},
        'capcode' : {'N': 1111}
    })
    
    success = client.post('/', data=data, headers=headers)
    assert(success.status_code == 204)
    assert(b"You are not authorised to use this service" not in success.data)
    assert(b"Error retrieving unit details" not in success.data)
    assert(len(success.data) == 0)

    expected_calls = [
            call(ses_id=None, ses_password=None),
            call().send(1111, data['Body'])
    ]
    assert(mock_viper.mock_calls == expected_calls)

    # TODO: Test page_log entry
