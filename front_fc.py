# -*- coding: utf-8 -*-

import os
import fc2
import logging

def handler(environ, start_response):
    logger = logging.getLogger()
    logger.info('============= Front FC Start ==============')
    logger.info(environ)

    msg_to_slack = None

    SLACK_TOKEN = os.environ['SLACK_TOKEN']
    SLACK_CHANNEL = os.environ['SLACK_CHANNEL']
    FUNCTION_COMPUTE_ENDPOINT = os.environ['FUNCTION_COMPUTE_ENDPOINT']
    # Example: ECS_CMD_CODE = ['start' 'stop']
    ECS_CMD_CODE = os.environ['ECS_CMD_CODE']

    # STS Token of FC Role
    ACCESS_KEY_ID = environ['accessKeyID']
    ACCESS_KEY_SECRET = environ['accessKeySecret']
    SECRET_TOKEN = environ['securityToken']

    FUNCTION_COMPUTE_SERVICE = environ['topic']
    INVOKE_FC = os.environ['INVOKE_FC']

    # SLACK_INFO
    # [
    #     'token=*****', 
    #     'team_id=*****',
    #     'team_domain=*****', 
    #     'channel_id=*****', 
    #     'channel_name=*****', 
    #     'user_id=*****', 
    #     'user_name=*****',
    #     'command=*****', 
    #     'text=<command>+<instance id>....',
    #     'response_url=https%3A%2F%2F*****'
    # ]
    SLACK_INFO = environ['QUERY_STRING'].split("&")
    TOKEN_INFO = SLACK_INFO[0].split("=")
    CHANNEL_INFO = SLACK_INFO[4].split("=")
    TEXT_INFO = SLACK_INFO[8].split("=")
    PARAMS = TEXT_INFO[1].split("+")
    ECS_CMD = PARAMS[0]
    RESPONSE_URL_INFO = SLACK_INFO[9].split("=")

    if TOKEN_INFO[1] != SLACK_TOKEN or CHANNEL_INFO[1] != SLACK_CHANNEL:
        msg_to_slack = '[Err] Unanthorized Slack domain [ ' + TOKEN_INFO[1] + ' ] or channel [ ' + CHANNEL_INFO[1] + ' ] !'
        logger.error(msg_to_slack)

    if len(PARAMS) < 2 or len(PARAMS) > 3:
        msg_to_slack = '[Err] Incorrect Params ! Please check your /ecs command !'
        logger.error(msg_to_slack)

    if ECS_CMD not in ECS_CMD_CODE:
        msg_to_slack = '[Err] Incorrect command : /ecs ' + ECS_CMD + '\n You can only use *' + ECS_CMD_CODE +'*'
        logger.error(msg_to_slack)

    if msg_to_slack is not None:
        msg_to_slack = bytes(msg_to_slack, 'utf-8')
        status = '200 OK'
        response_headers = [('Content-type', 'text/plain')]
        start_response(status, response_headers)
        return [msg_to_slack]


    ################
    #  FC
    ################
    client = fc2.Client(
        endpoint = FUNCTION_COMPUTE_ENDPOINT,
        accessKeyID = ACCESS_KEY_ID,
        accessKeySecret = ACCESS_KEY_SECRET,
        securityToken = SECRET_TOKEN
    )

    client.invoke_function(
        FUNCTION_COMPUTE_SERVICE,
        INVOKE_FC,
        headers = {'x-fc-invocation-type': 'Async'},
        payload = TEXT_INFO[1] + '&' + RESPONSE_URL_INFO[1] + '&' + SLACK_CHANNEL + '&' + ACCESS_KEY_ID + '&' + ACCESS_KEY_SECRET + '&' + SECRET_TOKEN
    )

    msg_to_slack = '[Info] Run /ecs '
    for data in PARAMS:
        msg_to_slack += data
    msg_to_slack = bytes(msg_to_slack, 'utf-8')

    status = '200 OK'
    response_headers = [('Content-type', 'text/plain')]
    start_response(status, response_headers)
    return [msg_to_slack]
