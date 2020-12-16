Twitter API V2
===

The new Twitter API is nothing like the old one. This is both good and bad. These scripts authenticate with the new API through a `BEARER_TOKEN` and handle pagination and rate-limiting.

The end result is a stream or file of line-delimited JSON representing a tweet object that is similar to the old API. It will embed user objects and additional includes into tweets as needed.


# Usage

    $ ./query.py [--token] QUERY_CONFIG_FILE
    
So, to run with the default `query_config.yaml` file: 

    $ ./query.py ./query_config.yaml


## Query Configurations:

`query_config.yaml` is a sample configuration file. The program can read query configurations in either 