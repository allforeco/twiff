import json
import logging
import datetime

from typing import *

from abc import ABC, abstractmethod

log = logging.getLogger(__name__)


class Parser(ABC):
    """ Base Parser Class for extracting information fields from input object, specific implementations
        should override the `__call__` method for extracting data from the object (usually a freeform text
        field) and return the parser data in the user-specified format to be used by other processes.
            
        CONTRACT:
            Returned data should be in the following format; response generator should only attempt to create
            a response if the "response" field is "success" likewise the retweet condition is the same.
            
            dParsed = {"response": "success",
                       "data": {"num_people": nPeople,
                                "created_at": tDate.strftime("%d-%m-%Y"),
                                "organization": sOrganisation,
                                "location": sFullLocation,
                                "url": sURL},
                       "errors": None}
                       
       NOTE:
            Returned key, value pairs should contain necessary information for the
            reponse_generator to select the approriate response. An example of how
            this is used is shown below.
    
        Args:
            tweet (Dict): Standard extended JSON tweet response.
        
        Returns:
            parsed_tweet (Dict): Parsed tweet data in JSON format.
            
        Example::
            >>> config = "/path/to/JSON"
            >>> parser = ParserChild(config)
            >>> result = parser(tweets)      
    """
    def __init__(self, config:str) -> None:
        '''
        Initialise the TweetParser instance.
        '''
        # Load configuration from JSON file.
        with open(config, "r") as fp:
            self.config = json.load(fp)
    
    @abstractmethod
    def __call__(self, tweet:Dict) -> Dict:
        '''
        Forward method to parse the tweet and return parsed data fields.
        '''
        pass  

    
class T4FParser(Parser):
    """ Parses tweet.

        NOTE:
            Returned key, value pairs should contain necessary information for the
            response_generator to select the appropriate response. An example of how
            this is used is shown below.

        Args:
            tweet (Dict): Standard extended JSON tweet response.

        Returns:
            parsed_tweet (Dict): Parsed tweet data in JSON format.
            response: success or failed
            tweettype: Normal or Quoted
            data: extracted twiff data
            errors: Possible errors are:
                hashtag_twiff_not_found
                twifftext_too_short
                no_org_found
                no_country_found
                no_city_found
                no_people_found

        Example::
            >>> config = "/path/to/JSON"
            >>> parser = TweetParser_v2(config)
            >>> result = parser(tweets, users)      
    """
    def __init__(self, config:str) -> None:
        '''
        Initialise the TweetParser_v2 instance.
        '''
        super(T4FParser, self).__init__(config)
        
        # Configuration
        self.BannedWords = self.config['banned_words']
        
    def __call__(self, tweet:Dict, users:list) -> Dict:
        '''
        Forward pass
        '''
        # To start parsing the twiff data, first extract some tweet data
        sTweetText = tweet["text"]
        dEntities = tweet["entities"]
        dUrls: []
        if "urls" in dEntities:
            dUrls = dEntities["urls"]
        tTweetDate = tweet["created_at"]
        
        # Let's find the start of the twiff string, drop the rest, not needed
        nTwiffStart = sTweetText.find("#twiff")
        if nTwiffStart < 0:
            nTwiffStart = sTweetText.find("#Twiff")
        if nTwiffStart < 0:
            nTwiffStart = sTweetText.find("#TWIFF")
        if nTwiffStart < 0:
            return {"response": "failed", "data": None, "errors": ["hashtag_twiff_not_found"]}
        sTwiffText = sTweetText[nTwiffStart:]
        
        # When the last URL is a display URL to a picture drop it too,
        # to prevent using the display URL as the quoted tweet parameter
        if "urls" in dEntities:
            for Url in dUrls:
                if "pic.twitter.com" in str(Url["display_url"]):
                    sDisplayUrl = str(Url["display_url"]).replace("pic.twitter.com/", "")
                    nLen = len(sTwiffText) - (len(sDisplayUrl) + 13)
                    sTwiffText = sTwiffText[:nLen]
                    break
                    
        # Find the correct tweet URL, for the tweet displaying the action
        # It may not necessarily be the reporting tweet
        sTweetUrl = ""
        sQuoteURL = ""
        sTweetType = "Normal"  # Remember tweet type for replies
        sQuotedUserId = ""
        if "referenced_tweets" in tweet:
            dRefTweets = tweet["referenced_tweets"]
            rft = {}
            for rft in dRefTweets:
                if rft["type"] == "quoted":
                    sTweetID = rft["id"]
                    sTweetType = "Quoted"
                    for Url in dUrls:
                        if sTweetID in str(Url["expanded_url"]):
                            sTweetUrl = Url["expanded_url"]
                            sQuoteURL = Url["url"]
                            sQuotedUserName = sTweetUrl.split("/")[3]
                            sQuotedUserId = FindUserIdByName_v2(users, sQuotedUserName)
                    break
                    
        if sTweetUrl == "":
            sUserId = tweet["author_id"]
            sUserName = FindUserNameById_v2(users, sUserId)
            sTweetUrl = "https://twitter.com/" + sUserName + "/status/" + tweet["id"]
            
        # Parse the twiff
        dParsed = self.TwiffParser_v2(sTwiffText, tTweetDate, sTweetUrl, sQuoteURL)
        
        # Check for banned words
        if any(word in sTweetText.split() for word in self.BannedWords["single_words"]):
            dParsed["response"] = "failed"
            dParsed["errors"] = AddError_v2(dParsed["errors"], "banned_word")
        elif any(word in sTweetText for word in self.BannedWords["multi_words"]):
            dParsed["response"] = "failed"
            dParsed["errors"] = AddError_v2(dParsed["errors"], "banned_word")
            
        dParsed["tweettype"] = sTweetType
        
        return dParsed

    def TwiffParser_v2(self, TwiffText, TweetDate, TweetURL, QuoteURL) -> Dict:
        '''
        # Let's see if we can extract twiff data from the tweet
        # Us machines need to account for the fact that humans make mistakes,
        # so let's see if we can work with whatever the human gave us.
        
            Args:
                TwiffText (dtype): description
                TweetDate (dtype): description
                TweetURL (dtype): description
                QuoteURL (dtype): description
                
            Example::
                >>> vars = {}
                >>> result = TwiffParser_v2(**vars)
                >>> log.info(result)
        
        '''        
        # TwiffText is a string that only contains twiff data, can it contain useful information?
        # primary check to prevent errors in the next section
        aErrors = []
        if len(TwiffText) < 10:
            return {"response": "failed", "data": None, "errors": AddError_v2(aErrors, "twifftext_too_short")}

        # let's assume the 6th character is a delimiter,
        # Unless that is a space, then check for a delimiter after the space, or numbers.
        i = 6
        while TwiffText[i:i + 1] == " " or TwiffText[i:i + 1].isnumeric() or TwiffText[i:i + 1].isalpha():
            i += 1
        sDelimiter = TwiffText[i:i + 1]
        TwiffText = TwiffText[6:]
        
        # remove the quote URL if needed
        if QuoteURL != "":
            TwiffText = TwiffText.replace(QuoteURL, "")
            
        # Also cut out when a new line is started
        if "\n" in TwiffText:
            TwiffText = TwiffText.split("\n")[0]
            
        # TwiffText is a string that only contains twiff data, can it contain useful information?
        # secondary check to see if continuing is useful
        if len(TwiffText) < 10:
            return {"response": "failed", "data": None, "errors": AddError_v2(aErrors, "twifftext_too_short")}
        
        # Now we know the delimiter, create the datafields
        sDatafields = TwiffText.split(sDelimiter)
        
        # Clean up actions
        i = 0
        while i < len(sDatafields):
            sDatafields[i] = sDatafields[i].strip(" ()[]{}#\n")  # Sometime people use brackets :\
            i += 1
            
        # Let's try to get some results
        nPeople = 0  # Expected as parameter 0
        sOrganisation = ""  # Expected as parameter 1
        sCountry = ""  # Expected as parameter 2
        sState = ""  # Expected as parameter 3
        sCity = ""  # Expected as parameter 4
        tDate: datetime = None  # Expected as parameter 5
        sURL = ""  # Expected as parameter 6
        
        # But humans aren't perfect, so they'll probs mess up :)
        for sDatafield in sDatafields:
            if sDatafield == "":
                continue
            # If it's a number is must be the numer of people (0)
            if sDatafield.isnumeric() and nPeople == 0:  # 20220415 Added 0 check
                nPeople = int(sDatafield)
                continue
            # If it starts with a number, and is between 6 and 10 chars long, it must be the date(5)
            if sDatafield[0:2].isnumeric():
                bOK, tDate = TryParseDateOnly_v2(sDatafield)
                if not bOK:
                    tDate = None
                continue
            # The rest are text strings, we can only check for URLs
            if sDatafield.startswith("http"):
                sURL = sDatafield
                continue
            # Otherwise let's hope people used the right order
            if sOrganisation == "":
                sOrganisation = sDatafield
                continue
            if sCountry == "":
                sCountry = sDatafield
                continue
            if sState == "":
                sState = sDatafield
                continue
            if sCity == "":
                sCity = sDatafield
                continue
                
        # We now came out of a very long loop checking twiff data letter by letter
        # If we don't have a city, but do have a state, the state was probs omitted
        if sState != "" and sCity == "":
            sCity = sState
            sState = ""
            
        # If no date was found, use tweet date
        if tDate is None:
            tDate = datetime.datetime.strptime(TweetDate, "%Y-%m-%dT%H:%M:%S.000Z")
            
        if sURL == "":
            sURL = TweetURL

        # Clean up locations
        if "." in sCountry:
            sCountry = sCountry.split(".")[0]
        if "." in sState:
            sState = sState.split(".")[0]
        if "." in sCity:
            sCity = sCity.split(".")[0]

        # We now made the most of the data as we could, let's do some basic checks before reporting
        if len(sOrganisation) < 3 or len(sOrganisation) > 50 or "http" in sOrganisation:
            aErrors = AddError_v2(aErrors, "no_org_found")
        if len(sCountry) < 2 or len(sCountry) > 35 or "http" in sCountry:
            aErrors = AddError_v2(aErrors, "no_country_found")
        if len(sState) > 35 or "http" in sState:
            aErrors = AddError_v2(aErrors, "no_state_found")
        if len(sCity) > 60 or "http" in sCity:
            aErrors = AddError_v2(aErrors, "no_city_found")
        if nPeople == 0:
            aErrors = AddError_v2(aErrors, "no_people_found")
            
        # Report back the results
        dParsed: dict
        sFullLocation = sCountry
        if sState != "":
            sFullLocation = sFullLocation + " " + sState
        sFullLocation = sFullLocation + " " + sCity
        if len(aErrors) > 0:
            dParsed = {"response": "failed",
                       "data": {"num_people": nPeople,
                                "created_at": tDate.strftime("%d-%m-%Y"),
                                "organization": sOrganisation,
                                "location": sFullLocation,
                                "url": sURL},
                       "errors": aErrors}
        else:
            dParsed = {"response": "success",
                       "data": {"num_people": nPeople,
                                "created_at": tDate.strftime("%d-%m-%Y"),
                                "organization": sOrganisation,
                                "location": sFullLocation,
                                "url": sURL},
                       "errors": None}
        return dParsed


def FindUserNameById_v2(users:Dict, userID:str):
    user = {}
    for user in users.values():
        if user["id"] == userID:
            return user["username"]

def FindUserIdByName_v2(users:Dict, userName:str):
    user = {}
    for user in users.values():
        if user["username"] == userName:
            return user["id"]

def AddError_v2(errors:list, newError: str) -> []:
    if errors is None:
        errors = [newError]
    else:
        errors.append(newError)
    return errors

def TryParseDateOnly_v2(DateTimeString:str):
    # Parses 4 formats, year always 4 digits
    # 1 when / is used in the string American annotation is assumed
    #      1.1 Year first or month first: 2000/31/12 or 12/31/2000
    # 2 any other delimiter EU standard is assumed
    #      2.1 Year first or day first: 31-12-2000 or 2000-12-31
    tDate: datetime = datetime.datetime.now()
    # sDate = tDate.strftime("%d-%m-%Y")
    
    # First check if this has any chance of success
    if len(DateTimeString) != 10:
        return False, tDate
    
    # Is the year in the first place?
    if DateTimeString[4:5].isnumeric():
        # If so split by the char in 3rd place
        sNumbers = DateTimeString.split(DateTimeString[2:3])
        # is the delimiter a / (american style)
        if DateTimeString[2:3] == "/":
            # American style, convert to EU style, date first
            sDate = sNumbers[1] + "-" + sNumbers[0] + "-" + sNumbers[2]
        else:
            # No conversion needed, but make sure -'s are in, not any other delimiter
            sDate = sNumbers[0] + "-" + sNumbers[1] + "-" + sNumbers[2]
    else:
        # If not split by the char in 5th place
        sNumbers = DateTimeString.split(DateTimeString[4:5])
        # is the delimiter a / (american style)
        if DateTimeString[4:5] == "/":
            # American style, convert to EU style, date first
            sDate = sNumbers[1] + "-" + sNumbers[2] + "-" + sNumbers[0]
        else:
            # Rotate so year goes last
            sDate = sNumbers[2] + "-" + sNumbers[1] + "-" + sNumbers[0]
            
    tDate = datetime.datetime.strptime(sDate, "%d-%m-%Y")
    
    return True, tDate




























































# import re
# import time
# import datetime
# import torchtext
# import dateparser

# from typing import *

# class TweetParser:
#     """ Parses tweet.
    
#         NOTE:
#             Returned key, value pairs should contain necessary information for the
#             reponse_generator to select the approriate response. An example of how
#             this is used is shown below.
    
#         Args:
#             tweet (Dict): Standard extended JSON tweet response.
        
#         Returns:
#             parsed_tweet (Dict): Parsed tweet data in JSON format.
            
#         Example::
#             >>> X
#             >>> Y
#     """
#     def __init__(self) -> None:
#         pass
    
#     def __call__(tweet:Dict) -> Dict:
#         pass  

    
# class SimpleParser(TweetParser):
#     def __init__(self) -> None:
#         super(SimpleParser, self).__init__()
        
#     def __call__(self, tweet:Dict) -> Dict:
#         # Retrieve text from tweet
#         text = tweet['text'].lower()

#         # Remove data before '#twiff' token
#         token_idx = text.find('#twiff')
#         if token_idx:
#             text = text[token_idx+len('#twiff'):]

#         # Remove data after 'http' token
#         token_idx = text.find('http')
#         if token_idx:
#             text = text[:token_idx]

#         # Slight cleaning of tokens
#         tokens = [item.strip() for item in text.split(',') if item!='']

#         # Extract number of people
#         num_people = num_people_from_tokens(tokens)

#         # Remove integer tokens
#         tokens = remove_integer_tokens(tokens)

#         if num_people:
#             parsed_tweet = {
#                 "response": "success",
#                 "data": {
#                     "num_people":num_people, 
#                     "created_at":tweet['created_at'], 
#                     "organization":tokens[0], 
#                     "location":', '.join(tokens[1:])
#                 }
#             }
#         else:
#             parsed_tweet = {
#                 "response":"failed",
#                 "data":None
#             }

#         return parsed_tweet


# def num_people_from_tokens(tokens):
#     # Search for first token with run of 1
#     run = 0
#     num_people = None
#     for tdx, token in enumerate(tokens):
#         # Attempt to convert token to integer format - accumulate number of integers encountered.
#         try:
#             int(token)
#             run += 1
#         except:
#             if run==1:
#                 num_people = tokens[tdx-1]
#                 break
#             run = 0
        
#     return num_people

# def remove_integer_tokens(tokens):   
#     # Remove any other integer from tokens
#     int_idxs = []
#     for tdx, token in enumerate(tokens):
#         try:
#             int(token)
#             int_idxs.append(tdx)
#         except:
#             pass
#     for int_idx in int_idxs[::-1]:
#         del tokens[int_idx]
        
#     return tokens

# def remove_integers_from_tokens(tokens):
#     for tdx, token in enumerate(tokens):
#         token = token.strip().lower()
#         token = remove_emoji(token)
#         token = re.sub('[,:;(){}##/?@!.\[\]&%$*^\+=|<>`~"\']', ' ', token)
        
#         sub_tokens = torchtext.data.get_tokenizer("basic_english")(token)
        
#         int_idxs = []
#         for idx, sub_token in enumerate(sub_tokens):
#             try:
#                 int(sub_token)
#                 int_idxs.append(idx)
#             except:
#                 pass
        
#         for int_idx in int_idxs[::-1]:
#             del sub_tokens[int_idx]
            
#         tokens[tdx] = ''.join(sub_tokens)
    
#     return tokens

# -----------------------------------------------------
# ---------------- New code from here -----------------
# -----------------------------------------------------

# Added _v2 to the new methods as some conflict with existing methods

