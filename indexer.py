import json
import os
import re
import pickle
import sys

from bs4 import BeautifulSoup
from collections import defaultdict
from nltk.stem import PorterStemmer

class Indexer:
    def __init__(self):
        self.directory_path = "../DEV/helpdesk_ics_uci_edu"
        self.doc_id = 0 
        self.stemmer = PorterStemmer()
        self.partial_count = 0
        self.size_threshold = 10 * 1024 * 1024 # 10 MB

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
        # inverted_index: {
        #     "token": {
        #         "document_frequency": int,
        #         doc_id: {
        #             "token_frequency: int,
        #             "weight": int
        #         }
        #     }
        # }
        self.inverted_index = {}
            
    def parse_files(self):
        # subdir - current directory being visited
        # dirs - subdirectories in the current subdir
        # files - list of files in current subdir
        print(123)
        for subdir, dirs, files in os.walk(self.directory_path):
            print(456)
            for file in files:
                file_path = os.path.join(subdir, file)

                # print(f"current file {doc_id}: ", file_path)

                with open(file_path, "r") as file:
                    try:
                        data = json.load(file)
                        soup = BeautifulSoup(data["content"], 'lxml')

                        # tokenizes document's html content & updates index
                        self.tokenize(soup)

                        if sys.getsizeof(self.inverted_index) > self.size_threshold:
                            self.offload()
                            self.inverted_index.clear()

                        # write partial index to file
                    except Exception as e:
                        raise e
                        print("error: ", e)
                    
                self.doc_id += 1

        if self.inverted_index:
            self.offload()
    

    def tokenize(self, soup):
        words = defaultdict(int) # Keeps track of tokens and their occurrences

        for tag in soup.find_all():
            tokens = re.split("[^a-zA-Z0-9']+", tag.text.lower())
            for token in tokens:
                token = self.stemmer.stem(token) 

                if token not in self.inverted_index:
                    self.inverted_index[token] = {"document_frequency": 0, "doc_ids": {}}
                if token in self.inverted_index and self.doc_id in self.inverted_index[token]["doc_ids"]:
                    self.inverted_index[token]["doc_ids"][self.doc_id]["weight"] += self.weights.get(tag.name, 1)

                words[token] += 1
        
        for key, value in words.items():
            self.inverted_index[key]["document_frequency"] += 1
            self.inverted_index[key]["doc_ids"][self.doc_id] = {"token_frequency": value, "weight": 0}
    

    def offload(self):
        filename = f'temporary_save_{self.partial_count}.pkl'
        with open(filename, "wb") as file:
            pickle.dump(self.inverted_index, file)
        self.partial_count += 1


    def merge(self):
        """
        Retrieving data from different pickle files
        """
        result_index = {}
        for i in range(self.partial_count):
            filename = f'temporary_save_{i}.pkl'
            
            with open(filename, "rb") as file:
                partial = pickle.load(file)
                
                for key, value in partial.items():
                    if key not in result_index:
                        result_index[key] = {"document_frequency": 0}

                    for doc_id, info in value.items():
                        if doc_id not in result_index[key]:
                            result_index[key][doc_id] = info
                            result_index[key]["document_frequency"] += 1

                        else:
                            result_index[key][doc_id]["token_frequency"] += info["token_frequency"]
                            result_index[key][doc_id]["weight"] += info["weight"]

        return result_index




if __name__ == '__main__':
    indexer = Indexer()
    indexer.parse_files()
    result = merge()