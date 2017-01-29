
# Creating Term-Document Matrix from Elasticsearch

####Tutorial by Animesh Pandey, email: apanimesh061@gmail.com
***
There have been many questions about how can we create a Term-Document matrix from an ElasticSearch index. I tried out a possible way which I think should work well. I will be starting from scratch and this whole method is divided into three parts

1. Initialising Index
2. Indexing documents
3. Querying for Term-Vectors
4. Creating a Term-Document Matrix

####Libraries used:

1. Python Version: 2.7.4 with Numpy/Scipy
2. ElasticSearch Version: 1.6.0


## Initialising Index

Since, a few of my the python files that I was importing were in a local directory, I had to import the directory in to the Python path using:


```python
import sys
sys.path.insert(0, 'C:\Users\Animesh\Documents\Presentation_07_07')
```

***
Following is the content of the file _constants.py_ which contains the constants that will be freqentry used in the whole application.
Here `ES_CLIENT` is the client of the elasticsearch that I'll be connecting to. `INDEX_NAME`, `TYPE_NAME` etc. are the constants defining the name of the index, document type etc. I have two different type of analyzers which also have been initialzed here.


```python
# This is constants.py
from elasticsearch import Elasticsearch

ES_HOST = {"host" : "localhost", "port" : 9200}
INDEX_NAME = 'social_media'
TYPE_NAME = 'tweet'
ANALYZER_NAME = 'my_english'
ANALYZER_NAME_SHINGLE = "my_english_shingle"
ES_CLIENT = Elasticsearch(hosts = [ES_HOST], timeout = 180)
```

***
Now, we will initialize the index. Notice that I have imported the _constants.py_ file to access the required values while creating the index. The function `init_index()` has two parts.
1. Settings: This is the set up of the index i.e. configuration of the index. `constants.ES_CLIENT.indices.create` helps in creating an index with soe settings.
2. Mapping: `press_mapping` is like the schema of the index. This defines that how the document will look like. Think of this thing like the SQL's `CREATE TABLE ...` where you specify which column will hold what type of data. Purpose of `"dynamic": "strict"` is raise an error if a document does not comply with the format specified in mapping. `constants.ES_CLIENT.indices.put_mapping` helps us add the mapping to the index.


```python
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
```

Now if you send a CURL command `curl -X GET "http://localhost:9200/social_media"?pretty=true` you will get the same `setings` and `mappings` as the response from ElasticSearch.

## Indexing Documents

Now that we have our index, we'll have to start indexing data into the index. Tweets are the best thing if you want something short and simple. For getting the tweets I used the `TwitterAPI`. `constants` is the constants file and `index_tweets` is the file where we had `init_index()`. I will talk about `util.py` later.


```python
from TwitterAPI import TwitterAPI
from elasticsearch import Elasticsearch
import constants, index_tweets, util
import cPickle
```

Using the `TwitterAPI` I will retireve the top 10 tweets under the handle name `elastic`. For interacting with Twitter API you need the authentication tokens, whic you can get from Twitter's [Developer Portal](https://dev.twitter.com/).


```python
SCREEN_NAME = 'elastic'

CONSUMER_KEY = ''
CONSUMER_SECRET = ''
ACCESS_TOKEN_KEY = ''
ACCESS_TOKEN_SECRET = ''
```

***
Here, I initialize the index `INDEX_NAME` and I send a request to the API to give me the tweets. The response JSON has a lot more than just text. You can view the whole respose skeleton [here](https://dev.twitter.com/rest/reference/get/statuses/user_timeline).

`TEMP_DOC` is the document that I will index. This document should comply with the schema that I have mentioned in the mapping of the index, otherwise it will raise an error. `constants.ES_CLIENT.index` is used to index the tweet in the index `INDEX_NAME`.


```python
api = TwitterAPI(CONSUMER_KEY,
                 CONSUMER_SECRET,
                 ACCESS_TOKEN_KEY,
                 ACCESS_TOKEN_SECRET)

r = api.request('statuses/user_timeline',
                {
                    'screen_name': SCREEN_NAME,
                    'count': 10
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
```

    The index has been initialised!
    Successfully indexed Tweet 629241463797366784 with id 0
    Successfully indexed Tweet 629216039339978752 with id 1
    Successfully indexed Tweet 629060379155431424 with id 2
    Successfully indexed Tweet 628949758166470656 with id 3
    Successfully indexed Tweet 628614404196696065 with id 4
    Successfully indexed Tweet 628601038690480128 with id 5
    Successfully indexed Tweet 628591924212051968 with id 6
    Successfully indexed Tweet 628578918396641280 with id 7
    Successfully indexed Tweet 628267050927063040 with id 8
    Successfully indexed Tweet 628255353168228352 with id 9
    

    E:\Python27\Lib\site-packages\requests\packages\urllib3\util\ssl_.py:90: InsecurePlatformWarning: A true SSLContext object is not available. This prevents urllib3 from configuring SSL appropriately and may cause certain SSL connections to fail. For more information, see https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning.
      InsecurePlatformWarning
    

***
Now we come to a very important part. If you look at the previous code, you'll notice `doc_index_map` which is actually a hash/dictionary that maps the orignal identifier of the tweet to an index represented by a number e.g. now tweet _629060379155431424_ will now be identified as _2_. This comes handy when you are dealing with creation of matrices which we'll talk about in a while.

The following are two functions from the `util.py` which save dictionaries to the hard-disk for future use. `doc_index_map.pkl` is the dictionary of the documnent identifier to a number. `vocab.pkl` is a similar type of hash but terms. i.e. this holds the complete vocabulary/unique terms in the 10 document index.


```python
util.createPickleFromDict(doc_index_map, "doc_index_map.pkl")
util.saveVocabulary()
```

    Pickled doc_index_map.pkl
    Pickled vocab.pkl
    

## Querying for Term-Vectors

Here we'll talk about the `util.py` file and its importance in the code. This file holds the functions that are required frequently by the application like reading the index, getting the term-vectors of a document, serialising of dictionaries, creation of the vocabulary etc.


```python
import constants
from elasticsearch import Elasticsearch
import cPickle

TERM_INDEX = 0
VOCAB = dict()
```

`loadPickle` loads the serialized pickle file where `name` of the path to the pickle file.


```python
def loadPickle(name):
    print "Loading " + name
    with open(name, 'rb') as f:
        return cPickle.load(f)
```

`createPickleFromDict` serializes a dictionary `d` to the `filename` specified.


```python
def createPickleFromDict(d,  filename):
    cPickle.dump(d,  open(filename,  "wb"))
    print 'Pickled ' + filename
```

`getTermVector` returns the term_vector of the documents having document id `doc_id`. We mainly require the term-frequencies of the terms mapped to their original term. We return this mapping(`temp`) along with the document's id(`a["_id"]`).


```python
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
```

`scrollIndex` scans through the index without loads all results into memory. So, with every document we get, we get its term_vector using `getTermVector`.


```python
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
```

`saveVocabulary` makes a pass through the whole index and creates a vocabulary (list of the unique terms) from that index and finally serializes it to the hard-disk as `vocab.pkl`. This explains _In [8]_ entry above.


```python
def getVocabulary(term_vector):
    global VOCAB
    global TERM_INDEX
    for term in term_vector:
        if term not in VOCAB.keys():
            VOCAB.update({term : TERM_INDEX})
            TERM_INDEX += 1

def saveVocabulary():
    for _, vector in scrollIndex():
        getVocabulary(vector.keys())
    createPickleFromDict(VOCAB, "vocab.pkl")
```

## Creating a Term-Document Matrix

At this point we have all the documents and dictionaries that we require. We'll now start with how the interpret what ever we have to a Matrix.


```python
import util
import numpy as np
from scipy.sparse import csr_matrix
```

Let us now load the dctionaries that we created. If you have a lot of documents I suggest using MongoDB for storing the mappings.


```python
term_map = util.loadPickle("vocab.pkl")
doc_map = util.loadPickle("doc_index_map.pkl")

no_of_terms = len(term_map)
no_of_docs = len(doc_map)
```

    Loading vocab.pkl
    Loading doc_index_map.pkl
    

I won't be going in detail about what a Sparse representation of a matrix is. The outputs that we get from ElasticSearch can easliy be translated into a Compressed Row Sparse Format. You can read about this represetation from internet. Using `ROW_OFFSETS`, `COLUMN_INDICES` and `VALUES` you can recreate the whole rectaungular Term-Document Matrix.


```python
# Creating a Compressed Row Sparse Format of the to be made Term-Document Matrix
ROW_OFFSETS = [0]
COLUMN_INDICES = []
VALUES = []
for doc, vector in util.scrollIndex():
    prev_offset = ROW_OFFSETS[-1]
    ROW_OFFSETS.append(prev_offset + len(vector))
    [(COLUMN_INDICES.append(term_map[term]), VALUES.append(count['tf'])) for (term, count) in vector.iteritems()]

print "The Compressed Sparse Row format:"
print
print "The row offsets:", ROW_OFFSETS # There can be takes as the Document IDs
print
print "The index of the term as per the vocab.pkl:"
print COLUMN_INDICES
print
print "The term-frequencies of the terms in COLUMN_INDICES on the same indices"
print VALUES
```

    The Compressed Sparse Row format:
    
    The row offsets: [0, 16, 34, 47, 60, 70, 86, 98, 113, 125, 141]
    
    The index of the term as per the vocab.pkl:
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 7, 27, 28, 29, 30, 31, 11, 32, 18, 33, 34, 23, 25, 35, 36, 11, 28, 37, 38, 39, 40, 41, 18, 42, 43, 44, 11, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 18, 55, 7, 56, 57, 11, 58, 59, 60, 18, 19, 61, 62, 38, 32, 23, 63, 11, 21, 20, 25, 64, 17, 65, 66, 67, 68, 69, 7, 9, 70, 71, 72, 11, 73, 20, 19, 74, 75, 76, 77, 18, 78, 7, 21, 79, 80, 81, 11, 82, 83, 84, 85, 18, 86, 87, 11, 88, 7, 89, 90, 17, 91, 92, 93, 19, 94, 61, 18, 64, 95, 7, 21, 20, 96, 97, 11]
    
    The term-frequencies of the terms in COLUMN_INDICES on the same indices
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 1, 1, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    

I have not used `termVectorFromCSR` anywhere but this function gives you the term_vector for each document where `doc_id` is the document ID, `indices[start : end]` is the list storing the term IDs and `data[start : end]` stores the term-frequencies of the terms in `indices[start : end]`.


```python
def termVectorFromCSR(row_offsets, indices, data):
    offsets = zip(row_offsets[::], row_offsets[1::])
    doc_id = 0
    for (start, end) in offsets:
        yield doc_id, indices[start : end], data[start : end]
        doc_id += 1
```

Finally, we have the Sparse Matrix and now we will utilise _Numpy/Scipy_ libraries to create a Dense Matrix out of the Sparse representation. The Rows are documents and Columns are the terms. The values are the term-frequencies. Now we can do whatever we want to do with `tdm` i.e. the term-document matrix.


```python
# Creating a Dense (Term-Document) Matrix using scipy and numpy
indptr = np.asarray(ROW_OFFSETS)
indices = np.asarray(COLUMN_INDICES)
data = np.asarray(VALUES)
tdm = csr_matrix((data, indices, indptr), shape=(no_of_docs, no_of_terms)).toarray()

print tdm # This is the Dense Version of the Sparse Matrix from ElasticSearch
```

    [[1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 1 0 0 0 1 0 0 0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 0 0 0 0 1 0 1 0 0 1 0 0 0 1 1 1 1 1
      1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0 0 2 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 1 1 1 1 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 2 0 0 0 1 0 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 2 1 1 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 0 0 0 0 1 0 0 0 0 0 0 1 1 1 1 0 1 0 1 0 0 0 0 0 0 1 0 0 0 0
      0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 1 0 1 0 1 0 0 0 0 0 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 1 0 0 0 1 0 0 0 0 0 0 1 1 2 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1
      1 1 2 1 1 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 1 0 0 0 2 0 0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 1 2 1 1 1 1 1 1 1 0 0 0 0 0 0 0]
     [0 0 0 0 0 0 0 1 0 0 0 1 0 0 0 0 0 1 1 1 1 1 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0 0 1 0 0 0 0 0 0 0 0 0
      0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1]]

