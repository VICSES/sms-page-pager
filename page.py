# Copyright 2017 David Tulloh
# This file is part of sms-page-pager. sms-page-pager is free software,
# you can distribute or modify it under the terms of the AGPL-3 licence.

import re
import os
import logging
import decimal
import time
from functools import wraps

from flask import Flask, request, abort, current_app
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse
from vicses.viper import Viper

import boto3
import botocore

app = Flask(__name__)
dynamodb = None


def get_table(table):
    global dynamodb
    if dynamodb is None:
        aws = boto3.Session()
        dynamodb = aws.resource('dynamodb', region_name='ap-southeast-2', use_ssl=True)
    return dynamodb.Table('sms-page-'+os.environ.get('STAGE')+'-'+table)


def lookup_contact_by_num(num):
    try:
        table = get_table('contact')
        response = table.get_item(Key={'phone_number':num})
    except botocore.exceptions.ClientError:
        return None
    return response.get('Item')


def lookup_unit_by_name(name):
    try:
        table = get_table('unit')
        response = table.get_item(Key={'name':name})
    except botocore.exceptions.ClientError:
        return None
    return response.get('Item') # NOTE: capcode is a Decimal


def insert_page_log(unit, phone_number, body):
    item = {
        'unit': unit,
        'timestamp': decimal.Decimal(str(time.time())),
        'phone_number': phone_number,
        'body': body,
    }

    print("III", item)

    try:
        get_table('page_log').put_item(Item=item)
    except botocore.exceptions.ClientError as err:
        logger = logging.getLogger(__name__)
        logger.error('insert_page_log %s', err)


# Decorator code provided in Twilio example
def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Create an instance of the RequestValidator class
        validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))

        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''))

        # Continue processing the request if it's valid, return a 403 error if
        # it's not
        if request_valid or current_app.debug:
            return f(*args, **kwargs)
        else:
            return abort(403)
    return decorated_function


def twiml_error(text):
    response = MessagingResponse()
    response.message(text)
    return response.to_xml()


@app.route("/", methods=['POST'])
@validate_twilio_request
def page():
    # From twilio
    body = request.form.get("Body")

    phone_number = re.sub("[^0-9]", "", request.form.get("From"))
    contact = lookup_contact_by_num(phone_number)
    if contact is None:
        return twiml_error("You are not authorised to use this service. Contact your unit management to register your phone number.")

    unit = lookup_unit_by_name(contact["unit"])
    if unit is None:
        return twiml_error("Error retrieving unit details, contact the systems administrator.")

    insert_page_log(contact["unit"], phone_number, body)

    viper = Viper(
        ses_id = os.environ.get('SES_ID'),
        ses_password = os.environ.get('SES_PASSWORD')
    )
    error = viper.send(int(unit["capcode"]), body)

    if error:
        return twiml_error("Error sending page, processing stalled at {}".format(error))

    return ('', 204) # No Content (success)
