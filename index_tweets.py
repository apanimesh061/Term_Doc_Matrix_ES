from elasticsearch import Elasticsearch
import constants

def init_index():
    constants.ES_CLIENT.indices.create(
        index = constants.INDEX_NAME,
        body = {
            "settings": {
                "index": {
                    "number_of_shards": 3,
                    "number_of_replicas": 0
                },
                "analysis": {
                    "analyzer": {
                        constants.ANALYZER_NAME: {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "asciifolding",
                                "cust_stop",
                                "my_snow"
                            ]
                        },
                        constants.ANALYZER_NAME_SHINGLE: {
                            "type": "custom",
                            "tokenizer": "standard",
                            "filter": [
                                "lowercase",
                                "asciifolding",
                                "cust_stop",
                                "my_snow",
                                "shingle_filter"
                            ]
                        }
                    },
                    "filter": {
                        "cust_stop": {
                            "type": "stop",
                            "stopwords_path": "stoplist.txt",
                        },
                        "shingle_filter" : {
                            "type" : "shingle",
                            "min_shingle_size" : 2,
                            "max_shingle_size" : 2,
                            "output_unigrams": True
                        },
                        "my_snow" : {
                            "type" : "snowball",
                            "language" : "English"
                        }
                    }
                }
            }
        }
    )

    press_mapping = {
        constants.TYPE_NAME: {
            "dynamic": "strict",
            "properties": {
                "_id": {
                    "type": "string",
                    "store": True,
                    "index": "not_analyzed"
                },
                "text": {
                    "type": "multi_field",
                    "fields": {
                        "text": {
                            "include_in_all": False,
                            "type": "string",
                            "store": False,
                            "index": "not_analyzed"
                        },
                        "_analyzed": {
                            "type": "string",
                            "store": True,
                            "index": "analyzed",
                            "term_vector": "with_positions_offsets",
                            "analyzer": constants.ANALYZER_NAME
                        },
                        "_analyzed_shingles": {
                            "type": "string",
                            "store": True,
                            "index": "analyzed",
                            "term_vector": "with_positions_offsets",
                            "analyzer": constants.ANALYZER_NAME_SHINGLE
                        }
                    }
                }
            }
        }
    }

    constants.ES_CLIENT.indices.put_mapping (
        index = constants.INDEX_NAME,
        doc_type = constants.TYPE_NAME,
        body = press_mapping
    )

    print "The index has been initialised!"

if __name__ == "__main__":
    init_index()
