import json
import math
import os
import re
import sys
import csv
import simhash
import Levenshtein
import time

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
        self.crawled_pages = set()
        self.crawled_urls = set()
        self.fingerprints = set()

        # dictionary with weights for different html tags
        self.weights = {
            'title': 5,
            'h1': 4.5,
            'h2': 4,
            'h3': 3.5,
            'h4': 3,
            'h5': 2.5,
            'h6': 2,
            'bold': 1,
            'strong': 1,
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
                        temp_url = urldefrag(data["url"]).url
                        self.addresses[self.doc_id] = temp_url

                        if temp_url not in self.crawled_urls:
                            token_frequencies = simhash.get_frequencies(soup.get_text())
                            fingerprint = simhash.get_fingerprint(token_frequencies)
                            similar = False
                            for f in self.fingerprints:
                                distance = Levenshtein.distance(fingerprint, f)
                                if distance < 1:
                                    similar = True
                                    self.fingerprints.add(fingerprint)
                                    break 
                            if similar:
                                self.doc_id += 1
                                continue
                            self.fingerprints.add(fingerprint)

                            # tokenizes document's html content & updates index
                            if self.tokenize(soup):
                                self.crawled_urls.add(temp_url)

                            # checks if the size of index exceeds the threshold
                                if sys.getsizeof(self.index) > self.size_threshold:
                                    self.offload()
                                    self.index.clear()
                                

                    except UnicodeDecodeError as e:
                        pass

                    except Exception as e:
                        print(e)

                self.doc_id += 1
                print(self.doc_id)

        # if the index is not empty, offload it
        if self.index:
            self.offload()
    

    def tokenize(self, soup):
        """
        Gets the text from the file and stem the words
        """
        # keeps track of tokens and the number of documents they appear in
        token_list = []
        words = defaultdict(int) 

        # splits the text into alphanumeric tokens 
        for token in re.split("[^a-zA-Z0-9']+", soup.get_text().lower()):
            # stems the token 
            token = token.strip()
            token = token.strip("\'")
            if token:
                stemmed = self.stemmer.stem(token)
                token_list.append(stemmed)

                # increments token count
                words[stemmed] += 1

        # Check for duplicate pages
        hash_value = hash(tuple(token_list))
        if hash_value in self.crawled_pages:
            return False

        self.crawled_pages.add(hash_value)

        # updates token's document frequency
        for key, value in words.items():
            if key not in self.index:
                self.index[key] = {"document_frequency": 0, self.doc_id: {}}
            self.index[key]["document_frequency"] += 1
            self.index[key][self.doc_id] = {"token_frequency": value/sum(words.values()), "weight": 0}

        # update the weights of each token based on its tag
        self.update_weights(soup)
        return True
    

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
        Offloads the data into JSON files
        """
        directory_path = "./res"
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)

        filename = f'{directory_path}/temporary_save_{self.partial_count}.json'
        with open(filename, "w") as file:
            json.dump(self.index, file)
        self.partial_count += 1


    def merge(self):
        """
        Retrieving data from different JSON files, creates a final data file and a reference index file
        """
        result_index = {}
        # Loops over every pkl file
        for i in range(self.partial_count):
            filename = f'./res/temporary_save_{i}.json'
            
            with open(filename, "r") as file:
                partial = json.load(file)
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
            idf = math.log(N / (df))
            for doc_id, info in postings.items():
                if doc_id != "document_frequency":
                    tf = info["token_frequency"]
                    if info["weight"] == 0:
                        result_index[token][doc_id]["token_frequency"] = tf * idf
                    else:
                        result_index[token][doc_id]["token_frequency"] = (tf * idf) * info["weight"]
                    # token_frequency now has tf-idf score

                    

        reference_index = {}             # Can be used later for seeking
        with open(f'./res/inverted_index.json', "w") as file:
            for token, data in result_index.items():
                index = file.tell()
                file.write(json.dumps({token: data}) + "\n")
                reference_index[token] = index

        with open('./res/inverted_index.csv', 'w', newline='') as csvfile:
            fieldnames = ['token', 'doc_id', 'token_frequency', 'weight']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for token, postings in result_index.items():
                for doc_id, info in postings.items():
                    if doc_id != "document_frequency":
                        writer.writerow({
                            'token': token,
                            'doc_id': doc_id,
                            'token_frequency': info['token_frequency'],
                            'weight': info['weight']
                        })

        with open('./res/reference_index.json', "w") as file:
            json.dump(reference_index, file)
        
        with open('./res/urls.json', "w") as file:
            json.dump(self.addresses, file)
        return result_index


if __name__ == '__main__':
    t = time.time()
    indexer = Indexer()
    indexer.parse_files()
    result = indexer.merge()

    print("Unique tokens:", len(indexer.index))
    print("Number of documents:", indexer.doc_id + 1)
    print("Time spent:", time.time() - t)
