# -*- coding: utf-8 -*-
import logging
import json
import os
import re
import urllib.parse
import requests
import time
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkecs.request.v20140526 import DescribeInstanceAttributeRequest
from aliyunsdkcore.auth.credentials import StsTokenCredential

def handler(event, context):
    logger = logging.getLogger()
    logger.info('------- Start execution Function Compute -------')

    START = 'start'
    STOP = 'stop'
    TOKYO_REGION_ID = 'ap-northeast-1'
    RUNNING_STATUS_CODE = 'Running'
    msg_to_slack = None

    event_data = event.decode('utf-8').split("&")
    logger.info(event_data)
    CMD_INFO = event_data[0]
    response_url = event_data[1]
    SLACK_CHANNEL = event_data[2]
    ACCESS_KEY_ID = event_data[3]
    ACCESS_KEY_SECRET = event_data[4]
    SECRET_TOKEN = event_data[5]

    # CMD: ["start" "<ECS instance id>"] or ["start" "<ECS instance id>" "<Region id>"]
    CMD = CMD_INFO.split("+")
    if len(CMD) == 2:
        REGION_ID = TOKYO_REGION_ID
    elif len(CMD) == 3:
        REGION_ID = CMD[2]

    ################
    #  ECS
    ################
    
    sts_token = StsTokenCredential(ACCESS_KEY_ID, ACCESS_KEY_SECRET, SECRET_TOKEN)
    client = AcsClient(credential=sts_token)

    #TODO
    # STOP
    if CMD[0] == START:
        request = CommonRequest()
        request.set_accept_format('json')
        request.set_domain('ecs.' + REGION_ID + '.aliyuncs.com')
        request.set_method('POST')
        request.set_protocol_type('https') # https | http
        request.set_version('2014-05-26')
        request.set_action_name('StartInstance')
        request.add_query_param('RegionId', REGION_ID)
        request.add_query_param('InstanceId', CMD[1])
        response = client.do_action(request)
        request.set_action_name('DescribeInstanceAttribute')
        request.add_query_param('RegionId', REGION_ID)
        request.add_query_param('InstanceId', CMD[1])

        tmp_response_data = client.do_action(request)
        response = json.loads(tmp_response_data)

    #logger.info(str(response, encoding = 'utf-8'))
    retry_count = 0
    while response["Status"] != RUNNING_STATUS_CODE:
        if retry_count == 15 :
            break
        logger.info(response["Status"])
        request.set_action_name('DescribeInstanceAttribute')
        tmp_response_data = client.do_action(request)
        response = json.loads(tmp_response_data)
        time.sleep(2)
        retry_count += 1

    if response["Status"] == RUNNING_STATUS_CODE :
        msg_to_slack = "[Info] ECS instance " + CMD[1] +  " is running now ! "
    else:
        msg_to_slack = "[Err] Something wrong when run the command: /ecs " + CMD[0] + ' ' + CMD[1] + " !"


    SLACK_WEBHOOK = urllib.parse.unquote(response_url)
    payload_dic = {
        "text": msg_to_slack,
        "channel": "#" + SLACK_CHANNEL
    }
    r = requests.post(SLACK_WEBHOOK, data=json.dumps(payload_dic))
