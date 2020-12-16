Twitter API V2
===

These scripts authenticate with the new API through a `BEARER_TOKEN` and handle pagination and rate-limiting.

The end result is a stream or file of line-delimited JSON representing a tweet object that is similar to the old API. It will embed user objects and additional includes into tweets as needed.

These scripts unpack and recombine metadata with individual tweets.


# Usage

    $ ./query.py [--token] QUERY_CONFIG_FILE
    
So, to run with the default `query_config.yaml` file: 

    $ ./query.py ./query_config.yaml


## Query Configurations:

`query_config.yaml` is a sample configuration file. The program can read query configurations in either YAML or JSON format.

See the Examples and Debugging Notebook for examples on how you can use this within a notebook or other scripts.