from TwitterAPI import TwitterAPI
from elasticsearch import Elasticsearch
import constants, index_tweets, util
import cPickle

SCREEN_NAME = 'elastic'

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_TOKEN_KEY = ''
ACCESS_TOKEN_SECRET = ''


api = TwitterAPI(CONSUMER_KEY,
                 CONSUMER_SECRET,
                 ACCESS_TOKEN_KEY,
                 ACCESS_TOKEN_SECRET)

r = api.request('statuses/user_timeline',
                {
                    'screen_name': SCREEN_NAME,
                    'count': 100
                })

doc_index = 0
doc_index_map = dict()

# initialise the index
index_tweets.init_index()

for item in r:
    TEMP_DOC = { "text": item['text'] }
    try:
        constants.ES_CLIENT.index(
                index=constants.INDEX_NAME,
                doc_type=constants.TYPE_NAME,
                body=TEMP_DOC,
                id=doc_index
        )
        print "Successfully indexed Tweet {tweet} with id {tweet_index}".format(tweet=item['id'], tweet_index=doc_index)
        doc_index_map.update({item['id'] : doc_index})
        doc_index += 1
    except Exception as e:
        print e
        print "Error for Tweet {tweet}".format(tweet=item['id'])

util.createPickleFromDict(doc_index_map, "doc_index_map.pkl")

print('\nQUOTA: %s' % r.get_rest_quota())
