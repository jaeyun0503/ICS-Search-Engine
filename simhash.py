from bs4 import BeautifulSoup
import re

def get_frequencies(text):
    word = ''
    token_list = []
    token_frequencies = {} # dict: key = token, value = frequency
    
    # iterate over each character in the file 
    for char in text:
        # if the character is a digit, add it to the current word
        if char.isdigit():
            word += char
        # if the character is an uppercase letter, convert it to lowercase and add it to the current word
        elif char >= 'A' and char <= 'Z':
            word += char.lower()
        # if the character is a lowercase letter, add it to the current word
        elif char >= 'a' and char <= 'z':
            word += char
        # if the character is not alphanumeric, append the current word to the token list and reset the word to an empty string
        else:
            if word:
                token_list.append(word)
                word = ''
                
    # after processing all characters, check if there's any remaining word and append it to the token list
    if word:
        token_list.append(word)
    
    # count frequency of every token in list
    for token in token_list:
        if token in token_frequencies:
            token_frequencies[token] += 1
        else:
            token_frequencies[token] = 1 # if token not in dict, add with count
    
    return token_frequencies

# Creates 16-bit binary for every token/word
def hash_to_bit_string(word):
    hash_value = 0

    for char in word:
        hash_value = (hash_value + ord(char)) % (2**16) # fits into max 16 bits

    bit_string = bin(hash_value)[2:].zfill(16)
    return bit_string

# Get the fingerprint for each webpage based on its tokens/words & their frequencies
def get_fingerprint(token_frequencies_dict):
    to_add = [[] for _ in range(16)]  # initialize 8 lists to store tokens in each group
    sum_of_weights = [0] * 16  # initialize a list to store the sum of weights for each group
    fingerprint = ""

    # convert tokens to 16-bit hash values and distribute them into 16 groups
    for token, frequency in token_frequencies_dict.items():
        token_value = 1
        # hash token by its first character to determine group
        group_index = ord(token[0]) % 16
        # hash token to bit string
        token_bit_string = hash_to_bit_string(token)

        if token_bit_string[7] == '0': # if 8th bit is 0, token_value will be -1
            token_value = -1 

        to_add[group_index].append(token_value * frequency)

    # calculate sum of weights for each group
    for i, group in enumerate(to_add):
        sum_of_weights[i] = sum(group)
    
    
    # for each sum in sum_of_weights, create the bit-string based on positive/negative sign of number
    for val in sum_of_weights:
        if val < 1:
            fingerprint += "0" # negative numbers are 0
        else:
            fingerprint += "1" # positive numbers are 1

    return fingerprint