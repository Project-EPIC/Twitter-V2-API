#!/usr/bin/python3

import os, json, time, requests, sys, yaml, argparse
from datetime import datetime

class QueryHandler():

    def __init__(self, headers, 
                       params={}, 
                       outfile="output.jsonseq",
                       write=True,
                       _print=False,
                       store=False):
        self._headers = headers
        self._params  = params

        if not params:
            raise Exception("No Empty Parameters Allowed")
        
        # What do we do with the tweets? 
        self._write = write
        self._store = store
        self._print = _print
        
        self._tweet_count = 0;

        # Set defaults
        self._next_token             = None
        self._requests_remaining     = 1;
        self._seconds_remaining      = 900
        self._results                = []
        if write: 
            self._outfile                = open(outfile, 'w')
    
        #Actually send off the first query:
        try: 
            data = self.hit_search_api()

            sys.stderr.write("Query Initialized; {} requests remaining and {} seconds until window resets:\n".format(
                                self._requests_remaining, self._seconds_remaining))


            if data:
                self._oldest_id = 't' + data.get('meta').get('oldest_id')
                self.parse_results(data)
                
                sys.stderr.write(json.dumps(data.get('meta'), indent=4))
                
                sys.stderr.write("Latest Tweet:\n")
                sys.stderr.write(json.dumps(data.get('data')[0], indent=4))

        except:
            raise
        
    def api_call(self):
        response = requests.request( "GET", 
                                 "https://api.twitter.com/2/tweets/search/all", 
                                 headers=self._headers, 
                                 params=self._params)
        self.update_header_meta(response.headers)

        if response.status_code==400:
            raise Exception("Error (most likely in your query parameters)")
        return response

    #There is a lot more than "data" in a tweet, there might be "includes" and "expansions" 
    def parse_results(self, data):
        self._meta        = data.get('meta')
        self._next_token  = self._meta.get('next_token')
        self._data        = data
        
        #Hopefully the most performant way to handle the optional fields, it will get big and ugly though...
        users = {}
        
        if self._meta.get('result_count'):
                        
            if data.get('includes'):
                #Build user lookup
                    if data.get('includes').get('users'):
                        for u in data.get('includes').get('users'):
                            users[u["id"]] = u

            for idx, t in enumerate( data.get('data') ):
            
                self._tweet_count+=1
                
                # Add user information
                if users.get(t['author_id']):
                    t['user'] = users.get(t['author_id'])
                
                if self._write:
                    self._outfile.write(json.dumps(t)+"\n")
                if self._store:
                    self._results.append(t)
                if self._print:
                    print(json.dumps(t))
            
    def update_header_meta(self, headers):
        self._requests_remaining   = int( headers.get('x-rate-limit-remaining') )
        self._seconds_remaining    = int( headers.get('x-rate-limit-reset') ) - int(time.time())
        
    def pause_then_query(self, message):
        sys.stderr.write("\n" + message + "\n")
        sys.stderr.write("TIME: "+str(datetime.now()))
        sys.stderr.write("Sleeping for {} seconds until window resets   ".format(self._seconds_remaining))
        
        for t in range(0, int(self._seconds_remaining/5)+1):
            sys.stderr.write("\rSleeping for {} seconds until window resets   ".format(self._seconds_remaining - 5*t))
            time.sleep(5)
        
        response = self.api_call()
        if response.status_code==200:
            return response.json()
        else:
            raise Exception(response.status_code, response.text)
            
    def hit_search_api(self):
        if self._requests_remaining > 0:
            response = self.api_call()
            if response.status_code==200:
                return response.json()
            elif response.status_code==429:
                self._error = response.text
                return self.pause_then_query("Rate Limit Exceeded")
        else:
            return self.pause_then_query("No more requests remaining in this window")        

    def get_all_tweets(self, limit=10):
        count = 1;
        while self._next_token:
            self._params['next_token'] = self._next_token
            
            data = self.hit_search_api()
            if data:
                self.parse_results(data)

            #Debugging
            count+=1
            if limit and count > limit:
                sys.stderr.write("\nhit limit, stopping; next_token: "+self._next_token)
                break
            if count%10==0:
                sys.stderr.write("\r{} Tweets | {} Requests | {} Requests Remaining        ".format(self._tweet_count, count, self._requests_remaining))
        sys.stderr.write("\nFinished; {} tweets | {} requests remaining".format(self._tweet_count, self._requests_remaining))
        self._outfile.close()
    

#Runtime 

parser = argparse.ArgumentParser(description='Submit historical query to Twitter API V2')

parser.add_argument('QUERY_CONFIG_FILE', metavar='QUERY_CONFIG_FILE', type=str,
                    help='Path to your query file (JSON or YAML)')

parser.add_argument('--token', metavar="BEARER_TOKEN", type=str, help='Bearer Token from an associated Twitter App')



        
if __name__ == "__main__":
    
    args = parser.parse_args()
    
    print("\Loading configuration file: " + args.QUERY_CONFIG_FILE)
    
    try:
        if args.QUERY_CONFIG_FILE.endswith(".json"):
            query_config = json.load(open(args.QUERY_CONFIG_FILE, 'r'))
        elif args.QUERY_CONFIG_FILE.endswith(".yaml"):
            query_config = yaml.safe_load(open(args.QUERY_CONFIG_FILE, 'r'))    
        else:
            query_config = yaml.safe_load(open(args.QUERY_CONFIG_FILE, 'r'))
    except:
        raise
        
    command_line_args = vars(args)
        

    # Check for a bearer token override: 
    TOKEN = os.environ['BEARER_TOKEN']
    
    if query_config.get('bearer_token'):
        TOKEN = query_config.get('bearer_token')
        
    if command_line_args.get('token'):
        TOKEN = command_line_args.get('token')

    HEADERS = {"Authorization": "Bearer {}".format(TOKEN)}
    
    # What do we do with the tweets? 
    output  = None
    _write  = False
    _print  = True
    _store  = False
    
    if query_config.get('print'):
        _print=True
        
    if query_config.get('print')==False:
        _print=False
    
    if query_config.get('output'):
        _write=True
        output = query_config.get("output")
        
    limit = query_config.get('limit')
    
    # Need to remove anything that's not a valid Twitter parameter
    query_config.pop('output', None)
    query_config.pop('store', None)
    query_config.pop('print', None)
    query_config.pop('bearer_token', None)
    query_config.pop('limit', None)
    
    sys.stderr.write(json.dumps(query_config, indent=4)+"\n")

    # And now we start!
    tweet_handler = QueryHandler(
        headers=HEADERS,
        _print=_print,
        store=_store,
        write=_write,
        outfile=output,
        params=query_config)
    
    tweet_handler.get_all_tweets(limit=limit)
    
   
    
    
#     print("Then initialize the object")
    
#     print("Then get all of the tweets")
    
#     print("Then be done")

    print("\ndone\n") 
    
    