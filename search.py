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


def calculate_tfidf(query, top_k=20):
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
                print(data)
                postings = data[token]
                for doc_id, info in postings.items():
                    if doc_id != "document_frequency":
                        doc_scores[doc_id] += info["token_frequency"]

    # Sort documents by their TF-IDF score
    sorted_docs = sorted(doc_scores.items(), key=lambda item: item[1], reverse=True)

    return sorted_docs[:top_k]


# def calculate_tfidf(query, top_k=20):
#     """
#     Calculate TF-IDF scores for query matching documents.
#     Only documents containing all tokens in the query are considered valid.
#     """
#     N = DOCUMENTS
#     doc_scores = defaultdict(float)
#     valid_documents = None  # To track intersection of document IDs across tokens

#     with open("./res/inverted_index.pkl", "rb") as file:
#         for token in query:
#             if token in reference_index:
#                 index = reference_index[token]
#                 file.seek(index)
#                 data = pickle.load(file)  # Load the token data
#                 print(data)
#                 postings = data[token]
                
#                 current_docs = set()  # Track current token document IDs
                
#                 # Collect document IDs and their scores if token_frequency is not zero
#                 for doc_id, info in postings.items():
#                     if doc_id != "document_frequency" and info["token_frequency"] > 0:
#                         current_docs.add(doc_id)
#                         doc_scores[doc_id] += info["token_frequency"]

#                 # Update valid_documents with the intersection of current_docs
#                 if valid_documents is None:
#                     valid_documents = current_docs
#                 else:
#                     print(valid_documents, current_docs)
#                     valid_documents.intersection_update(current_docs)

#     # Filter out scores for documents that do not contain all tokens
#     final_scores = {doc_id: score for doc_id, score in doc_scores.items() if doc_id in valid_documents}

#     # Sort documents by their TF-IDF score
#     sorted_docs = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)
    
#     return sorted_docs[:top_k]



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
        return_list = []
        for i in range(len(sorted_docs)):
            if urls[sorted_docs[i][0]] not in return_list:
                return_list.append(urls[sorted_docs[i][0]])
            if len(return_list) == 5:
                break

        print("\nTop 5 URLs:")

        for i in return_list:
            print(i)
        
        print("\nSearch time:", time.time() - t, "seconds")


if __name__ == "__main__":
    search() 
