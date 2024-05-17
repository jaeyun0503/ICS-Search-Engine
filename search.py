import re
from nltk.stem import PorterStemmer
import time
import pickle
import math

from indexer import *
from collections import defaultdict

reference_index = {}
urls = {}

DOCUMENTS = 55395

def tokenize_query(query):
    tokens = re.split("[^a-zA-Z0-9']+", query.lower())
    stemmer = PorterStemmer()
    return [stemmer.stem(token) for token in tokens]


# def calculate_tfidf(query, top_k=5):
#     """
#     Calculate TF-IDF scores for query matching documents
#     """
#     N = DOCUMENTS
#     doc_scores = defaultdict(float)
    

#     with open("./res/inverted_index.pkl", "rb") as file:
#         for token in query:
#             if token in reference_index: 
#                 index = reference_index[token]
#                 postings = file.seek(index)[token]
#                 for doc_id, info in postings.items():
#                     if doc_id != "document_frequency":
#                         doc_scores[doc_id] += info["token_frequency"]
        
#     # Sort documents by their TF-IDF score
#     sorted_docs = sorted(doc_scores.items(), key=lambda item: item[1], reverse=True)

#     return sorted_docs[:top_k]

def calculate_tfidf(query, top_k=5):
    """
    Calculate TF-IDF scores for query matching documents
    """
    N = DOCUMENTS
    doc_scores = defaultdict(float)

    with open("./res/inverted_index.pkl", "rb") as file:
        for token in query:
            if token in reference_index: 
                index = reference_index[token]
                file.seek(index)
                data = pickle.load(file) #use pickle.load
                postings = data[token]
                for doc_id, info in postings.items():
                    if doc_id != "document_frequency":
                        doc_scores[doc_id] += info["token_frequency"]

    # Sort documents by their TF-IDF score
    sorted_docs = sorted(doc_scores.items(), key=lambda item: item[1], reverse=True)

    return sorted_docs[:top_k]


def search():
    global reference_index, urls
    
    with open("./res/reference_index.pkl", "rb") as file:
        reference_index = pickle.load(file)

    with open("./res/urls.pkl", "rb") as file:
        urls = pickle.load(file)


    while True: 
        query = input("\nEnter your query (Type EXIT to exit the program): ")
        
        if query == "EXIT":
            break

        t = time.time()

        query_tokens = tokenize_query(query)
        sorted_docs = calculate_tfidf(query_tokens)
        # for each token, find index containing doc id of where that term occurs 
        # find common doc id btwn the tokens 
        # rank them ?? 
        # map the doc id(s) back to the url(s)

        print("\nTop 5 URLs:")

        for i in sorted_docs:
            print(urls[i[0]])
        
        print("\Search time:", time.time() - t, "seconds")


if __name__ == "__main__":
    search() 
