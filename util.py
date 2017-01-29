import constants
from elasticsearch import Elasticsearch
import cPickle
import re
import datetime, time

TERM_INDEX = 0
VOCAB = dict()

def loadPickle(name):
    print "Loading " + name
    with open(name, 'rb') as f:
        return cPickle.load(f)

def createPickleFromDict(d,  filename):
    cPickle.dump(d,  open(filename,  "wb"))
    print 'Pickled ' + filename

def getTermVector(doc_id):
    temp = dict()
    a = constants.ES_CLIENT.termvector(index = constants.INDEX_NAME,
                                    doc_type = constants.TYPE_NAME,
                                    id = doc_id,
                                    field_statistics = True,
                                    fields = ['text._analyzed'],
                                    term_statistics = True
                                )
    curr_termvec = a["term_vectors"]["text._analyzed"]["terms"]
    tokens = curr_termvec.keys()
    [temp.update({token : {"tf": curr_termvec[token]["term_freq"]}}) for token in tokens]
    return a["_id"], temp

def getVocabulary(term_vector):
    global VOCAB
    global TERM_INDEX
    for term in term_vector:
        if term not in VOCAB.keys():
            VOCAB.update({term : TERM_INDEX})
            TERM_INDEX += 1

def scrollIndex():
    ALL_QUERY = {"query": {"match_all": {}}}

    rs = constants.ES_CLIENT.search(
                index=constants.INDEX_NAME,
                scroll='60s',
                size=10,
                body=ALL_QUERY
            )

    data = rs['hits']['hits']
    for doc in data:
        curr_doc, curr_term_vector = getTermVector(doc["_id"])
        yield curr_doc, curr_term_vector

    scroll_size = rs['hits']['total']

    while scroll_size:
        try:
            scroll_id = rs['_scroll_id']
            rs = constants.ES_CLIENT.scroll(scroll_id=scroll_id, scroll='60s')
            data = rs['hits']['hits']
            for doc in data:
                curr_doc, curr_term_vector = getTermVector(doc["_id"])
                yield curr_doc, curr_term_vector

            scroll_size = len(rs['hits']['hits'])
        except Exception as e:
            print e

def saveVocabulary():
    for _, vector in scrollIndex():
        getVocabulary(vector.keys())
    createPickleFromDict(VOCAB, "vocab.pkl")

def deleteIndex(name):
    constants.ES_CLIENT.indices.delete(name)
    time.sleep(0.5)
    if not constants.ES_CLIENT.indices.exists(name):
        print name, "has been deleted successfully..."
