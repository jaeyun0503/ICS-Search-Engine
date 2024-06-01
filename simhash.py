from bs4 import BeautifulSoup
import re

def get_frequencies(text):
    word = ''
    token_list = []
    token_frequencies = {}
    
    for char in text:
        if char.isdigit():
            word += char
        elif char >= 'A' and char <= 'Z':
            word += char.lower()
        elif char >= 'a' and char <= 'z':
            word += char
        else:
            if word:
                token_list.append(word)
                word = ''
                
    if word:
        token_list.append(word)
    
    for token in token_list:
        if token in token_frequencies:
            token_frequencies[token] += 1
        else:
            token_frequencies[token] = 1
    
    return token_frequencies

def hash_to_bit_string(word):
    hash_value = 0

    for char in word:
        hash_value = (hash_value + ord(char)) % (2**16) 

    bit_string = bin(hash_value)[2:].zfill(16)
    return bit_string

def get_fingerprint(token_frequencies):
    to_add = [[] for _ in range(16)] 
    sum_of_weights = [0] * 16 
    fingerprint = ""

    for token, frequency in token_frequencies.items():
        token_value = 1
        group_index = ord(token[0]) % 16
        token_bit = hash_to_bit_string(token)

        if token_bit[7] == '0':
            token_value = -1 

        to_add[group_index].append(token_value * frequency)

    for i, group in enumerate(to_add):
        sum_of_weights[i] = sum(group)
    
    for val in sum_of_weights:
        if val < 1:
            fingerprint += "0"
        else:
            fingerprint += "1"

    return fingerprint