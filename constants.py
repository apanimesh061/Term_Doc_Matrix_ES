from elasticsearch import Elasticsearch

ES_HOST = {"host" : "localhost", "port" : 9200}
INDEX_NAME = 'social_media'
TYPE_NAME = 'tweet'
ANALYZER_NAME = 'my_english'
ANALYZER_NAME_SHINGLE = "my_english_shingle"
ES_CLIENT = Elasticsearch(hosts = [ES_HOST], timeout = 180)