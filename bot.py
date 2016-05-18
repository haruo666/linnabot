import json
import os
from logging import DEBUG, StreamHandler, getLogger
from functools import reduce

import requests

import doco.client
import falcon
import csv

# logger
logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)

ENDPOINT_URI = 'https://trialbot-api.line.me/v1/events'
PROXIES = {
    'http': os.environ.get('FIXIE_URL', ''),
    'https': os.environ.get('FIXIE_URL', '')
}
DOCOMO_API_KEY = os.environ.get('DOCOMO_API_KEY', '')


class CallbackResource(object):
    # line
    header = {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-Line-ChannelID': os.environ['LINE_CHANNEL_ID'],
        'X-Line-ChannelSecret': os.environ['LINE_CHANNEL_SECRET'],
        'X-Line-Trusted-User-With-ACL': os.environ['LINE_CHANNEL_MID'],
    }

    # docomo
    #user = {'t': 20}  # 20:kansai character
    user = {'place': '東京'}
    docomo_client = doco.client.Client(apikey=DOCOMO_API_KEY, user=user)

    def on_post(self, req, resp):

        body = req.stream.read()
        if not body:
            raise falcon.HTTPBadRequest('Empty request body',
                                        'A valid JSON document is required.')

        receive_params = json.loads(body.decode('utf-8'))
        logger.debug('receive_params: {}'.format(receive_params))

        for msg in receive_params['result']:

            logger.debug('msg: {}'.format(msg))
            converted_msg = reduce(lambda x, y: x.replace(y, dict[y]), reversed_dict, msg['content']['text'])
            logger.debug('converted_msg: {}'.format(converted_msg))

            try:
                docomo_res = self.docomo_client.send(
                    #utt=msg['content']['text'], apiname='Dialogue')
                    utt=converted_msg, apiname='Dialogue')

            except Exception:
                raise falcon.HTTPError(falcon.HTTP_503,
                                       'Docomo API Error. ',
                                       'Could not invoke docomo api.')

            logger.debug('docomo_res: {}'.format(docomo_res))

            res_utt = docomo_res['utt']
            converted_utt = reduce(lambda x, y: x.replace(y, dict[y]), dict, res_utt)

            send_content = {
                'to': [msg['content']['from']],
                'toChannel': 1383378250,  # Fixed value
                'eventType': '138311608800106203',  # Fixed value
                'content': {
                    'contentType': 1,
                    'toType': 1,
                    #'text': docomo_res['utt'],
                    'text': converted_utt,
                },
            }
            send_content = json.dumps(send_content)
            logger.debug('send_content: {}'.format(send_content))

            res = requests.post(ENDPOINT_URI, data=send_content,
                                headers=self.header, proxies=PROXIES)
            logger.debug('res: {} {}'.format(res.status_code, res.reason))

            resp.body = json.dumps('OK')


api = falcon.API()
api.add_route('/callback', CallbackResource())

# Load gyokai dictionary
dict={}
reverse_dict={}
with open('gyokai.csv') as fin:
    reader=csv.reader(fin, skipinitialspace=True, quotechar="'")
    for row in reader:
        dict[row[0]]=row[1]
        reverse_dict[row[1]]=row[0]

'''
dict = {
'男': 'ちゃんにー',
'男性': 'ちゃんにー',
'女': 'ちゃんねー',
'女性': 'ちゃんねー',
'予約する':'バミる',
'寿司':'シースー',
'お寿司':'シースー',
'一緒に':'バーターで',
'一緒':'バーター',
'ダメ':'NG',
'ハワイ':'ワイハ',
'どうですか':'どうよ',
'六本木':'ギロッポン',
'綺麗':'れいきー',
'です':'っす',
'ですよ':'っすね',
'本当':'まじ',
'とても':'超',
'食べる':'べるたー',
'食べた':'べるたーした',
'欲しい':'しいほー',
'ちょっと':'ちょいもう',
'大きい':'かいでー',
}
'''
