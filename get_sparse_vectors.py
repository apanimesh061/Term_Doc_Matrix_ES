import util
import numpy as np
from scipy.sparse import csr_matrix

def termVectorFromCSR(row_offsets, indices, data):
    offsets = zip(row_offsets[::], row_offsets[1::])
    doc_id = 0
    for (start, end) in offsets:
        yield doc_id, indices[start : end], data[start : end]
        doc_id += 1

term_map = util.loadPickle("vocab.pkl")
doc_map = util.loadPickle("doc_index_map.pkl")

no_of_terms = len(term_map)
no_of_docs = len(doc_map)

# Creating a Compressed Row Sparse Format of the Term-Document Matrix
ROW_OFFSETS = [0]
COLUMN_INDICES = []
VALUES = []
for doc, vector in util.scrollIndex():
    prev_offset = ROW_OFFSETS[-1]
    ROW_OFFSETS.append(prev_offset + len(vector))
    [(COLUMN_INDICES.append(term_map[term]), VALUES.append(count['tf'])) for (term, count) in vector.iteritems()]

print ROW_OFFSETS
print COLUMN_INDICES
print VALUES

# Creating a Dense (Term-Document) Matrix using scipy and numpy
indptr = np.asarray(ROW_OFFSETS)
indices = np.asarray(COLUMN_INDICES)
data = np.asarray(VALUES)
tdm = csr_matrix((data, indices, indptr), shape=(no_of_docs, no_of_terms)).toarray()

print tdm

for sparse_vector in termVectorFromCSR(ROW_OFFSETS, COLUMN_INDICES, VALUES):
    doc_index, term_index, tf = sparse_vector
    print doc_index, term_index, tf
