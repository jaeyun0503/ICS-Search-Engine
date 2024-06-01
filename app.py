from flask import Flask, request, render_template
import re
from nltk.stem import PorterStemmer
import time
import json
from collections import defaultdict

app = Flask(__name__)

reference_index = {}
urls = {}
DOCUMENTS = 55395

STOPWORDS = set(["a", "an", "the", "and", "or", "but", "if", "in", "on", "with", "as", "by", "for", "of", "at", "to"])

def tokenize_query(query):
    tokens = re.split("[^a-zA-Z0-9']+", query.lower())
    stemmer = PorterStemmer()
    stopwords_count = sum(1 for token in tokens if token in STOPWORDS)
    if stopwords_count > len(tokens) / 2:
        return [stemmer.stem(token) for token in tokens]
    else:
        return [stemmer.stem(token) for token in tokens if token not in STOPWORDS]

def calculate_tfidf(query, top_k=20):
    N = DOCUMENTS
    doc_scores = defaultdict(float)
    valid_documents = None

    with open("./res/inverted_index.json", "r") as file:
        for token in query:
            if token in reference_index:
                index = reference_index[token]
                file.seek(index)
                line = file.readline()
                data = json.loads(line)
                postings = data[token]
                
                current_docs = set()
                for doc_id, info in postings.items():
                    if doc_id != "document_frequency" and info["token_frequency"] > 0:
                        current_docs.add(doc_id)
                        doc_scores[doc_id] += info["token_frequency"]

                if valid_documents is None:
                    valid_documents = current_docs
                else:
                    valid_documents.intersection_update(current_docs)

    final_scores = {doc_id: score for doc_id, score in doc_scores.items() if doc_id in valid_documents}
    sorted_docs = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)
    
    return sorted_docs

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    query_tokens = tokenize_query(query)
    sorted_docs = calculate_tfidf(query_tokens)

    return_list = []
    for i in range(len(sorted_docs)):
        if urls[sorted_docs[i][0]] not in return_list:
            return_list.append(urls[sorted_docs[i][0]])

    return render_template('results.html', query=query, results=return_list, count=len(sorted_docs))

if __name__ == "__main__":
    with open("./res/reference_index.json", "r") as file:
        reference_index = json.load(file)

    with open("./res/urls.json", "r") as file:
        urls = json.load(file)

    app.run(debug=True)
