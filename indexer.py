import json
import math
import os
import pickle
import re
import sys

from bs4 import BeautifulSoup
from collections import defaultdict
from nltk.stem import PorterStemmer
from urllib.parse import urldefrag

DOCUMENTS = 55395

class Indexer:
    def __init__(self):
        self.directory_path = "./DEV/"
        self.doc_id = 0                       # Number to keep track of document ID
        self.stemmer = PorterStemmer()        # Stemmer boohoo
        self.partial_count = 0                # Number to keep track of offloading
        self.size_threshold = 5 * 1024 * 1024 # 5 MB
        self.addresses = {}                    # For saving doc_ids to urls

        # dictionary with weights for different html tags
        self.weights = {
            'title': 50,
            'h1': 35,
            'h2': 30,
            'h3': 25,
            'h4': 20,
            'h5': 15,
            'h6': 10,
            'bold': 5,
            'strong': 5,
        }

        # index structure
        # index: {
        #     "token": {
        #         "document_frequency": int,
        #         doc_id: {
        #             "token_frequency": int,
        #             "weight": int
        #         }
        #     }
        # }
        self.index = dict()
            

    def parse_files(self):
        """
        Parses the json files under the directory
        """
        # subdir - current directory being visited
        # dirs - subdirectories in the current subdir
        # files - list of files in current subdir
        for subdir, dirs, files in os.walk(self.directory_path):
            for file in files:
                file_path = os.path.join(subdir, file)
                
                with open(file_path, "r") as file:
                    try:
                        # loads the json data from the file
                        data = json.load(file)
                        # parses the html content using lxml's html parser 
                        soup = BeautifulSoup(data["content"], 'lxml')

                        # tokenizes document's html content & updates index
                        self.tokenize(soup.get_text())
                        # update the weights of each token based on its tag
                        self.update_weights(soup)

                        # checks if the size of index exceeds the threshold
                        if sys.getsizeof(self.index) > self.size_threshold:
                            self.offload()
                            self.index.clear()
                        self.addresses[self.doc_id] = urldefrag(data["url"]).url

                    except Exception as e:
                        print("error: ", e)

                self.doc_id += 1

        # if the index is not empty, offload it
        if self.index:
            self.offload()
    

    def tokenize(self, text):
        """
        Gets the text from the file and stem the words
        """
        # keeps track of tokens and the number of documents they appear in
        words = defaultdict(int) 

        # splits the text into alphanumeric tokens 
        for token in re.split("[^a-zA-Z0-9']+", text.lower()):
            # stems the token 
            stemmed = self.stemmer.stem(token)

            # checks if the token is not already in the index, and updates it accordingly
            if token not in self.index:
                self.index[token] = {"document_frequency": 0, self.doc_id: {}}
            
            # increments token count
            words[token] += 1

        # updates token's document frequency
        for key, value in words.items():
            self.index[key]["document_frequency"] += 1
            self.index[key][self.doc_id] = {"token_frequency": value/sum(words.values()), "weight": 0}
    

    def update_weights(self, soup):
        """
        Update the weights of token in each document
        """
        for tag in soup.find_all():
            for word in re.split("[^a-zA-Z']+", tag.get_text().lower()):
                if word in self.index and self.doc_id in self.index[word]:
                    self.index[word][self.doc_id]["weight"] += self.weights.get(tag.name, 1)


    def offload(self):
        """
        Offloads the data into pkl files
        """
        directory_path = "./res"
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        filename = f'{directory_path}/temporary_save_{self.partial_count}.pkl'
        with open(filename, "wb") as file:
            pickle.dump(self.index, file)
        self.partial_count += 1


    def merge(self):
        """
        Retrieving data from different pickle files, creates a final data file and a reference index file
        """
        result_index = {}
        # Loops over every pkl file
        for i in range(self.partial_count):
            filename = f'./res/temporary_save_{i}.pkl'
            
            with open(filename, "rb") as file:
                partial = pickle.load(file)
                # key - token
                # value - token_dict
                for key, value in partial.items():
                    if key not in result_index:
                        result_index[key] = {"document_frequency": 0}
                    # key - token_frequency & doc_id
                    # value - token_frequency: int, doc_id: dict
                    for doc_id, info in value.items():
                        if doc_id == "document_frequency":
                            result_index[key]["document_frequency"] += info
                        else:
                            if doc_id not in result_index[key]:
                                result_index[key][doc_id] = {
                                    "token_frequency": 0,
                                    "weight": 0
                                }
                                result_index[key]["document_frequency"] += 1

                            result_index[key][doc_id]["token_frequency"] += info["token_frequency"]
                            result_index[key][doc_id]["weight"] += info["weight"]

            os.remove(filename)
        N = DOCUMENTS
        for token, postings in result_index.items():
            df = postings["document_frequency"]
            idf = math.log(N / (1 + df))
            for doc_id, info in postings.items():
                if doc_id != "document_frequency":
                    tf = info["token_frequency"]
                    if info["weight"] == 0:
                        result_index[token][doc_id]["token_frequency"] = tf * idf
                    else:
                        result_index[token][doc_id]["token_frequency"] = (tf * idf) * info["weight"]
                    # token_frequency now has tf-idf score

                    

        reference_index = {}             # Can be used later for seeking
        with open(f'./res/inverted_index.pkl', "wb") as file:
            for token, data in result_index.items():
                index = file.tell()
                pickle.dump({token: data}, file)
                reference_index[token] = index

        with open('./res/reference_index.pkl', "wb") as file:
            pickle.dump(reference_index, file)
        
        with open('./res/urls.pkl', "wb") as file:
            pickle.dump(self.addresses, file)
        return result_index


if __name__ == '__main__':

    indexer = Indexer()
    indexer.parse_files()
    result = indexer.merge()

    print("Unique tokens:", len(indexer.index))
    print("Number of documents:", indexer.doc_id + 1)
    # total = sum(os.path.getsize(f'./res/temporary_save_{i}.pkl') for i in range(indexer.partial_count)) / 1024
    # print("Total size in disk:", total, "KB")
