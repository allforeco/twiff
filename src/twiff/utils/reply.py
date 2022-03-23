import json

from pathlib import Path

from typing import *

class ReplyGenerator:
    """ ...
    """
    def __init__(self, path:str) -> None:
        self.path = Path(path)
        with open(self.path, 'r') as fp:
            self.responses = json.load(fp)
    
    def __call__(self, parsed_tweet:Dict) -> str:
        """ Generate reponse based on parsed_tweet.
        
            Args:
                parsed_tweet (Dict): Parsed tweet
                    response (str): Type of response suggested.
                    data (Dict): Parsed data.
                    
            Returns:
                response (str): Response text for the reply tweet.
        """
        if parsed_tweet['response']=='success':
            return self.responses['tweet-parse-success']
        else:
            return self.responses['tweet-parse-failed']