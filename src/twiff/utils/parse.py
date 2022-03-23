import re
import time
import datetime
import torchtext
import dateparser

from typing import *

class TweetParser:
    """ Parses tweet.
    
        NOTE:
            Returned key, value pairs should contain necessary information for the
            reponse_generator to select the approriate response. An example of how
            this is used is shown below.
    
        Args:
            tweet (Dict): Standard extended JSON tweet response.
        
        Returns:
            parsed_tweet (Dict): Parsed tweet data in JSON format.
            
        Example::
            >>> X
            >>> Y
    """
    def __init__(self) -> None:
        pass
    
    def __call__(tweet:Dict) -> Dict:
        pass  

    
class SimpleParser(TweetParser):
    def __init__(self) -> None:
        super(SimpleParser, self).__init__()
        
    def __call__(self, tweet:Dict) -> Dict:
        # Retrieve text from tweet
        text = tweet['text'].lower()

        # Remove data before '#twiff' token
        token_idx = text.find('#twiff')
        if token_idx:
            text = text[token_idx+len('#twiff'):]

        # Remove data after 'http' token
        token_idx = text.find('http')
        if token_idx:
            text = text[:token_idx]

        # Slight cleaning of tokens
        tokens = [item.strip() for item in text.split(',') if item!='']

        # Extract number of people
        num_people = num_people_from_tokens(tokens)

        # Remove integer tokens
        tokens = remove_integer_tokens(tokens)

        if num_people:
            parsed_tweet = {"response":"success",
                            "data":{"num_people":num_people, 
                                    "created_at":tweet['created_at'], 
                                    "organization":tokens[0], 
                                    "location":', '.join(tokens[1:])
                                   }
                           }
        else:
            parsed_tweet = {"response":"failed",
                            "data":None
                           }

        return parsed_tweet
































def num_people_from_tokens(tokens):
    # Search for first token with run of 1
    run = 0
    num_people = None
    for tdx, token in enumerate(tokens):
        # Attempt to convert token to integer format - accumulate number of integers encountered.
        try:
            int(token)
            run += 1
        except:
            if run==1:
                num_people = tokens[tdx-1]
                break
            run = 0
        
    return num_people

def remove_integer_tokens(tokens):   
    # Remove any other integer from tokens
    int_idxs = []
    for tdx, token in enumerate(tokens):
        try:
            int(token)
            int_idxs.append(tdx)
        except:
            pass
    for int_idx in int_idxs[::-1]:
        del tokens[int_idx]
        
    return tokens

def remove_integers_from_tokens(tokens):
    for tdx, token in enumerate(tokens):
        token = token.strip().lower()
        token = remove_emoji(token)
        token = re.sub('[,:;(){}##/?@!.\[\]&%$*^\+=|<>`~"\']', ' ', token)
        
        sub_tokens = torchtext.data.get_tokenizer("basic_english")(token)
        
        int_idxs = []
        for idx, sub_token in enumerate(sub_tokens):
            try:
                int(sub_token)
                int_idxs.append(idx)
            except:
                pass
        
        for int_idx in int_idxs[::-1]:
            del sub_tokens[int_idx]
            
        tokens[tdx] = ''.join(sub_tokens)
    
    return tokens