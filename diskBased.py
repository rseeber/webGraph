import datetime
import requests
from bs4 import BeautifulSoup
import time
import urllib.robotparser as rp
import json
import networkx as nx
import signal
import sys
import socket

import logger
import graphHandler as gh
import scrape

# 2 weeks = 60 sec/min * 60 min/hr * 24 hr/day * 7 day/week * 2
RESOURCE_EXPIRY = 60 * 60 * 24 * 7 * 2

# 500 MiB
MAX_CACHE = 500 * pow(2, 20)
cache = {"example.com": {}, "google.com": {}}
cacheIndex = ["example.com", "google.com"]

#unused
def spiderDFS(url, depth):
    # get the domain of the url
    domain, page = scrape.splitURL(url)[0]
    # check if the domain is already on file
    filename = domainFilename(domain)
    edges = []
    #if so
    if filename:
        # open the file
        with open(filename, "r") as f:
            file = f.read()
        # parse it into a json-equivalent format
        json = json.loads(file)
        # check if the resource is recent
        if time.time() - json[domain][page]["!fetched"] > RESOURCE_EXPIRY:
            # TODO: re-fetch resource
            pass
        edges = json[domain][page]
    #if not
    else:
       # TODO: fetch resource 
       pass
    
    if depth >= scrape.maxDepth:
        pass
    for e in edges:
        spiderDFS(e, depth + 1)
    return
        
# unused
def appendNode(url):
    domain, page = scrape.splitURL(url)
    #check if the json exists for this domain
    #TODO

    # check if this page exists
    #TODO
        # if not, append it, with an empty list of edges

    # return the filename for them to open
    # TODO: cleanup
    return "filename.json"

# gets the json for this domain from cache if available, or else fetches from disk
def getJson(domain):
    # check if it's cached
    if domain in cache:
        # pull from the cache
        myJson = cache[domain]
    # if not, fetch it from the file on the disk
    else:
        myJson = getJson_disk(domain) # performs a file read

        # append it to the cache
        cacheIndex.append(domain)
        cache[domain] = myJson

        # prune cache if memory limits are reached
        # we update the disk during pruning
        pruneCache()


    return myJson

    
# return the json for this domain, creating one if it doesn't exist
def getJson_disk(domain):
    filename = f"data/{domain}.json"
    # Try to open the file
    try:
        with open(filename, "r") as f:
            file = f.read()
    # If not there, create the file
    except FileNotFoundError:
        # base data
        data = {"!metadata": [], domain: {}}
        # as prettified json (for human readability)
        data = json.dumps(data, sort_keys=True, indent=4)
        # save that string to the file
        with open(filename, "a") as f:
            f.write(data)

        # read the file
        with open(filename, "r") as f:
            file = f.read()

    # return the file as a python dict
    myJson = json.loads(file)
    return myJson
 
# takes myJson as a python dict, and overwrites the disk saved json with the new data
def updateJson_disk(myJson, domain):
    #set the filename
    filename = f"data/{domain}.json"

    # convert python dict to str
    data = json.dumps(myJson, sort_keys=True, indent=4)
    # overwrite the file with the new data
    with open(filename, "w") as f:
        f.write(data)
    return

# removes the oldest entries of the cache until memory limits are satisfied.
# the disk is updated to the new values of the cached item during pruning
def pruneCache():
    while len(json.dumps(cache)) > MAX_CACHE:
        # remove the oldest key
        oldestKey = cacheIndex.pop(0)
        # remove the corresponding oldest json
        updateJson_disk(cache.pop(oldestKey)) # update the disk


def updateCache(pageData, metaData, myJson, page, domain):
    pageData["metadata"] = metaData # fit metaData into pageData
    myJson[page] = pageData         # fit pageData into myJson
    cache[domain] = myJson          # fit myJson into the cache

# fetch the page, returning the updated pageData and metaData values for that page
def fetchPage(url, pageData, metaData):
    inlinks, outlinks, outdomains = scrape.parseWebpage(url)
    edges = inlinks + outlinks

    # update the pageData to match
    pageData["edges"] = edges
    # update the metadata
    metaData["age"] = time.time()
    metaData["color"] = "gray"

    return pageData, metaData



# visits a node, recursively tracing down until it hits a leaf or reaches maxDepth
def spiderDFS_visit(url: str, depth: int, maxDepth: int):

    # get the json for this domain as a python dict
    domain, page = scrape.splitURL(url)
    myJson = getJson(domain) # this has side effects on the cache potentially

    # check if the page has been visited before
    if page in myJson[domain]:
        pageData = myJson[domain][page]
        metaData = pageData["metadata"]
    # if this is our fist time on this node, add it to the graph
    else:
        # create the json for this specific page (we'll append it to myJson later)
        pageData = {"metadata":{}, "edges": []}
        metaData = pageData["metadata"]
        # set the metadata for this page
        metaData["color"] = "white"

    # Base Case #1
    # Stop digging if we've hit our maxDepth or if this is a no-go site
    if (depth >= maxDepth or not scrape.siteCheck(url)):
        # Notice that we don't set the color to black, since
        # we might come back on a spiderDFS_resume() call. 
        # So we keep it gray in order to denote the threshold 
        # of discovery.
        return

    # fetch the page if we haven't done so yet, or if it's expired
    edges = []
    if (metaData["color"] == "white") or (time.time() - metaData["age"] > RESOURCE_EXPIRY):
        pageData, metaData = fetchPage(domain)
    # or if we already have, then just save the edges from that data
    else:
        edges = pageData["edges"]

    # update the cache for our updates to the json
    updateCache(pageData, metaData, myJson, page, domain)

    # iterate through each of the adjacent nodes (shares an edge)
    for e in edges:
        # get info on the edge
        eDomain, ePage = scrape.splitURL(e)
        eJson = getJson(eDomain) # this func has side effects
        ePageData = eJson[eDomain][ePage]

        # Recursive Case
        ## we check for unvisited nodes
        if(ePageData["metadata"]["color"] == "white"):
            # Stop going deeper if we've been told to stop
            if scrape.interrupt:
                break
            # visit the child node, incrementing the depth by 1
            spiderDFS_visit(e, depth + 1, maxDepth)
        # Base Case #2
        else:
            pass
    # set the color as black after we've explored all the edges
    metaData["color"] = "black"
    updateCache(pageData, metaData, myJson, page, domain)