import datetime
import requests
from bs4 import BeautifulSoup
import time
import urllib.robotparser as rp
import json
import networkx as nx
import signal
import sys

import graphHandler as gh

# Create an empty graph to start
G = gh.Graph()
G_domain = gh.Graph()

# When set to true, the spider stops crawling deeper
interrupt = False
spider_started = False

robotCache = {}

class Data:
    # linkDict
    # >>> {
    #   link1: [link, link, link, ...],
    #   link2: [...],
    #   ...
    # }
    #
    # linkProgressDict
    # >>> [
    #   {link1: 10, link2: 10},     // n = 0
    #   {link3: 4, link4: 0, link5: 0, ...},    // n = 1
    #   ...                                     // ...
    # ]
    #
    # urlIndex      # type = set
    # >>> (link1, link2, ...)
    #

    def __init__(self, linkDict={}, linkProgressDict={}, urlIndex=set(())):
        self.linkDict = linkDict
        self.linkProgressList = linkProgressDict
        self.urlIndex = urlIndex
    def __str__(self):
        return f"{self.linkDict}, {self.linkProgressDict}, {self.urlIndex}"



# returns (domain, resource) as a 2-tuple of a URL. Does not verify input.
def splitURL(link, getDomain=""):
    # find the first "/" AFTER the protocol ("https://")
    start = 8
    if link.find("https://") < 0:
        start = 7
        if link.find("http://") < 0:
            start = 0
    split = link.find("/", start)
    # if there is no "/" at the end, that means there is no resource
    if split < 0:
        split = len(link)
        resource = ""
    else:
        # everything after the "/"
        resource = link[split+1:]
    # everything between "https://" and "/"
    domain = link[start:split]

    return domain, resource

# Returns Second-Level Domain of a provided domain
# 
def splitDomain(domain):
    return domain.split(".")

# fix local links, remove queries, end with a "/"
def standardizeLink(link, getDomain):
    # remove "mailto:" links
    if("mailto:" in link):
        return None

    # convert local links to regular links
    if("https://" not in link and "http://" not in link):
        if(link.find("/") == 0):
            link = "https://"+getDomain+link
        else:
            link = "https://"+getDomain+"/"+link
    # remove queries ("?key=value")
    queryIndex = link.find("?")
    if(queryIndex > -1):
        link = link[0:queryIndex]

    # remove page jumps ("example.com/home#header1")
    jumpIndex = link.find("#")
    if(jumpIndex > -1):
        link = link[0:jumpIndex]
    
    
    # ensure all links end with "/"
    if(link[-1] != "/"):
        link = link + "/"

    # Don't interact with onion links (they don't resolve properly over DNS anyways)
    if (splitURL(link)[0].endswith(".onion")):
        return None
    
    return link

def parseWebpage(pageURL):
    getDomain, getResource = splitURL(pageURL)
    retry = 0
    baseDelay = robotsCheck(pageURL)[1]
    # even if they didn't specifically mention a delay in their robots.txt,
    # let's be courtieous and wait 0.5 seconds between requests
    if baseDelay == 0:
        baseDelay = 0.5
    while(retry < 3):
        print("Fetching resource: "+pageURL)
        delay = 5 * retry + baseDelay
        print("Waiting "+str(delay)+" seconds...")
        # 1, 6, 11, 16 seconds, etc
        time.sleep(delay)
        try:
            reqs = requests.get(pageURL, headers=requestHeaders)
            soup = BeautifulSoup(reqs.text, 'html.parser')
            break
        except Exception:
            print("Exception caught. Retrying...")
            retry += 1

    inlinks = []
    outlinks = []
    outdomains = []

    # If we weren't able to fetch the page, return empty lists
    if(retry == 3):
        return inlinks, outlinks, outdomains

    # iterate through each <a> tag
    for a in soup.find_all('a'):
        # get the link
        link = a.get('href')
        # ignore broken or missing links
        if link == None:
            continue
        # standardize it
        link = standardizeLink(link, getDomain) 
        # input validation
        if link == None or link == "":
            continue

        # Isolate the domain
        domain, resource = splitURL(link)

        # same domain -> inlinks
        if(domain == getDomain):
            inlinks.append(link)
        # different domain (or subdomain) -> outlinks
        else:
            outlinks.append(link)
            outdomains.append(domain)

    
    return inlinks, outlinks, outdomains

# adds the edge if it is unique, or else increments the counter
def addEdge(myEdge, edges):
    # myEdge
    # >>> (from, to)
    # edges
    # >>> {(from, to): cnt, ...}
    
    # if we've already got this edge, just increment the count
    try:
        edges[myEdge]
        edges[myEdge] = edges[myEdge] + 1
    # otherwise, add it to the dict
    except Exception:
        edges[myEdge] = 1

# deprecated in favor of countUrls()
def buildGraph(links, currentUrl, urls, edges, domainEdges):

    # iterate through each discovered link, adding an edge from the current page to that link
    for link in links:

        # add link to urls if it's not from one of the untracked domains
        domain, resource = splitURL(link)
        track = True
        # go through each untracked domain
        for u in untrackedDomains:
            # if our domain is a subdomain of the untracked domains, ignore it
            if u in domain:
                track = False
        # otherwise, add it
        if(track):
            urls.add(link)

        # update edges
        myEdge = (currentUrl, link)
        addEdge(myEdge, edges)

        # update domainEdges
        myEdge = (splitURL(currentUrl)[0], splitURL(link)[0])  # e.g. (fromDomain, toDomain)
        addEdge(myEdge, domainEdges)

# replaces buildGraph()
def countUrls(links, urls):
    # iterate through each discovered link, adding an edge from the current page to that link
    for link in links:

        # add link to urls if it's not from one of the untracked domains
        domain, resource = splitURL(link)
        track = True
        # go through each untracked domain
        for u in untrackedDomains:
            # if our domain is a subdomain of the untracked domains, ignore it
            if domain.endswith(u):
                track = False
        # otherwise, add it
        if(track):
            urls.add(link)

# returns True if the url is allowed to be scraped
def robotsCheck(url):
    domain, resource = splitURL(url)
    global robotCache

    if domain not in robotCache:
        rfp = rp.RobotFileParser()
        rfp.set_url("http://"+domain+"/robots.txt")
        retry = 0
        while(retry < 10):
            try:
                rfp.read()
                break
            except:
                retry += 1
                print(f"Couldn't get robots file for {domain}. Waiting {5*retry} seconds...")
                time.sleep(5 * retry)
        else:
            print("Couldn't get resource. Skipping check.")
            return True, 0


        delay = rfp.crawl_delay(requestHeaders["User-Agent"])
        if delay == None:
            delay = 0

        allowed = rfp.can_fetch(requestHeaders["User-Agent"], url)
        if allowed == None:
            allowed = rfp.can_fetch("*", url)
        
        # save to cache
        robotCache.update({domain: [allowed, delay]})
    else:
        # load from cache
        allowed = robotCache[domain][0]
        delay = robotCache[domain][1]

    return allowed, delay

# depricated in favor of just using a library (wrapped up inside of robotsCheck())
def getRobotsTxt(domain):
    # see if we already have it cached
    if domain in robotsTxt:
        robo = robotsTxt[domain]
    # if not, go fetch it
    else:
        reqs = requests.get(domain+"/robots.txt", requestHeaders)
        # if the file isn't a 404
        if(reqs.status_code <= 400):
            robo = reqs.text
        # save it as an empty string if they don't have a robots.txt file
        else:
            robo = ""

        # select just the bit we want
        # search for "User-Agent: *"
        start = robo.find("User-Agent: *")
        # if it isn't there, none of this applies to us
        end = -1
        if start != -1:
            # search for another instance of User-Agent
            end = robo.find("User-Agent: ", start)
            # now that we have our endpoints, grab the substring that applies to us
            robo = robo[start:]
            if end != -1:
                robo = robo[start:end]


        # then cache whatever we saved
        robotsTxt.update({domain: robo})
    

    

# Given a list of urls to start with, it calls parseWebpage() on each. Then, it recursively goes through each of *those*.
# The function continues until it has found and saved all links N degrees or less from each provided url.
# In order to continue crawling at a higher degree, simply provide the returned data object.
def spider(startUrls, N, untrackedDomains, data=Data(), i=0):

    # if this is the first iteration, initialize the data
    if(i == 0):
        print("START SPIDER CRAWL")
        """
        data = {
            "startUrls": startUrls,
            "searchDepth": N,
            # Note: this will be a list of lists so that
            # data["Urls"][i] is the list of urls found at distance i from the startUrls
            "Urls":set(()),
            # a dict of the form {edge, cnt}, where edge is a 2-tuple of 
            # the form (from, to)), and cnt is an int
            "edges": {},
            # same format as above
            "domainEdges": {},
            # of the form {domain: ["bannedResource", "bannedResource", ... ], ... }
            "robots.txt": {}
        }
        """

        linkDict = {}
        linkProgressDict = {}
        urlIndex = set(())

        data = Data(linkDict, linkProgressDict, urlIndex)

    # Base case
    if(N <= 0):
        return data

    
    # Recursive Case

    # edges should be 2-tuples of the form (from, to)
    domainEdges = {}
    edges = {}

    # big list of all the links we've collected this round
    urls = set(())

    robotsTxt = {}

    linkCount = 0 
    # iterate through the provided pages
    for url in startUrls:
        # check robots.txt




        

        print("waiting 1 second before fetching resource "+url)
        time.sleep(1)
        # Parse the page
        inlinks, outlinks, outdomains = parseWebpage(url)

        data.linkDict.update({url: inlinks+outlinks})
        data.linkProgressDict.update({url:0})

        countUrls(inlinks+outlinks, urls)

        data.urlIndex.update(urls)

        # fill out urls, edges, and domainEdges with data from the parsed page
        #buildGraph(inlinks + outlinks, url, urls, edges, domainEdges)

        # display some data for the user
        print("urls found: "+str(urls))
        print("url count = "+str(len(urls)))
        linkCount += 1
        if(linkCount >= 10):
            break

    # Update the data object
    ## Note: since this is to be a list of lists, append() is correct (don't use extend()!!)
    #data[2].update(urls)
    ## Add the edges
    #data["edges"].update(edges)
    #data["domainEdges"].update(domainEdges)

    # recursion call
    print("REPEAT SPIDER CALL ON "+str(urls))
    # parse the first k links in each link set
    k = 10
    return spider(urls, N-1, untrackedDomains, data, i+1)

def spiderBetter(startUrls, N, data=Data(), j=0):
    if(j == 0):
        data.linkDict = {}
        data.linkProgressList = []
        data.urlIndex = set(())

    # Do the first K urls in set 1
    #save them to linkDict

    # loop:
        # Do the first K urls in linkDict which are not yet finished
        # save those to the linkDict
        # increment n counter
        # stop when n == N

    
    bigK = 10
    # iterate through each DEPTH LEVEL (each depth level is a unique collection of links)
    for n in range(N):
        # get the n'th dict in linkProgressList
        layer = data.linkProgressList[n]

        # iterate through the first i pages at depth n
        for i in range(len(data.linkProgressList[n])):
            # in that, get the i'th key
            parentLink = layer.keys()[i]

            # iterate through the first k CHILDREN of that page
            for k in range(bigK):
                # with that key, access the list of urls at linkDict[key]
                # myUrl = the k'th url in that list of urls
                myUrl = data.linkDict[parentLink][k]
                
                #myUrl = data.linkDict[data.linkProgressList[n].keys()[i]][k]

                # skip finished urls (for continuing search from a save file)
                if data.linkProgressList[i][myUrl] >= k:
                    continue

                # fetch the page and collect links
                inlinks, outlinks, outdomains = parseWebpage(myUrl)
                # add 
                data.linkDict.update({myUrl : inlinks})
                data.linkProgressDict.update({startUrls[j] : 0})

# spider using Depth-First Search algorithm, using Q as your starting nodes,
# and crawling a maximum distance of `depth` from any of the starting nodes.
def spiderDFS(startingNodes, maxDepth):
    global spider_started
    spider_started = True
    # Assign all our "starting nodes" as unvisited
    for u in startingNodes:
        u.color = "white"
    # Keep crawling until we've finished our DFS on each starting node
    while len(startingNodes) > 0:
        # Dequeue an item from the front of the line
        u = startingNodes.pop(0)
        # Note: In Intro To Algorithms by CLRS, they only run DRF_visit() if u.color == white.
        # We don't do that, since we are placing a depth constraint.
        #
        # Basically, even though a longer path may have already discovered u, we check it again
        # because this time we set u.dist to 0, instead of a higher number on that longer path.
        # If we didn't care about distance from starting nodes, we wouldn't be doing this.
        #
        # Also, since fetching the webpage is much much slower than doing graph math,
        # we can treat retracing our paths as having lower Big O time than the original
        # fetching of the webpage, which only happens once, even if we retrace the node.
        spiderDFS_visit(u, 0, maxDepth)
        if interrupt:
            break

# returns true if you should fetch the site, false otherwise.
# It's based on both the untrackedDomains, and (eventually) the robots.txt protocol
def siteCheck(url):
    track = True
    for d in untrackedDomains:
        if d in url:
            track = False

    # put a robots.txt check here eventually
    
    return track

# visits a node, recursively tracing down until it hits a leaf or reaches maxDepth
def spiderDFS_visit(u: gh.Vertex, depth: int, maxDepth: int):
    print(f"Depth: {depth}")
    # if this is our fist time on this node, add it to the graph
    if(u.color == "white"):
        G.V.append(u)
        # also update the domain graph if this is a new domain
        domain, resource = splitURL(u.url)
        if(domain not in G_domain):
            G_domain.V.append(gh.Vertex(domain))

    u.dist = depth
    u.color = "gray"
    
    # Base Case #1
    # Stop digging if we've hit our maxDepth or if this is a no-go site
    if (depth >= maxDepth or not siteCheck(u.url)):
        # Notice that we don't set the color to black, since
        # we might come back on a spiderDFS_resume() call. 
        # So we keep it gray in order to denote the threshold 
        # of discovery.
        return

    # iterate through each of the adjacent nodes (shares an edge)
    for v in u.getAdjacent():
        # Create the edge in the graph
        G.addEdge(gh.Edge(u, v))

        # and in the domain graph
        G_domain.addEdge_url(splitURL(u.url)[0], splitURL(v.url)[0])

        # Recursive Case
        ## we check unvisited nodes, as well as nodes who have "unoptimized" paths
        ## (see my explanation inside spiderDFS())
        if (v.color == "white") or (v.dist > u.dist + 1):
            # Stop going deeper if we've been told to stop
            if interrupt:
                break
            # visit the child node, incrementing the depth by 1
            spiderDFS_visit(v, depth + 1, maxDepth)
        # Base Case #2
        else:
            pass
    u.color = "black"

# after having finished spiderDFS to a given depth, you can call spiderDFS_resume in order
# to crawl to a deeper depth. Not intended to resume from a crash or outage.
# Recall that G = (V, E)
#
# NOTE: this will have the effect of *resetting* depth of grey nodes to zero,
# essentially restarting the crawl on them instead
# to just start at your starting nodes, doing depth normally, call spiderDFS() normally
def spiderDFS_resume(maxDepth):
    startingNodes = []
    for v in G.V:
        if v.color != "black":
            startingNodes.append(v)
    spiderDFS(startingNodes, maxDepth)
    return G

# probably not using this one. Just call spiderDFS() yourself.
def spiderDFS_init(startingNodes, maxDepth):
    G = gh.Graph()
    spiderDFS(G, startingNodes, maxDepth)

    return G


robotsTxt = {}
requestHeaders = {"User-Agent":"WebGraphUtility", "From":"riverseeber12@gmail.com"}


def getTimestamp():
    dt = datetime.datetime.now()
    timestamp = f"{str(dt.year)}-{str(dt.month)}-{str(dt.day)}_{str(dt.hour)}-{str(dt.minute)}-{str(dt.second)}"
    return timestamp

# This function is called when Ctrl+C is pressed
def interrupt_handler(sig, frame):
    global interrupt
    # On the first interrupt, close gracefully
    # If the spider hasn't started, just close (nothing started yet)
    if not interrupt and spider_started:
        print("\nINTERRUPT SIGNAL RECIEVED: Closing gracefully...")
        print("(to force quit, send the interrupt again)")
    else:
        exit()
    # To keep track of if this is the first interrupt
    interrupt = True


if __name__ == "__main__":
    # register interrupt_handler() to be called when pressing Ctrl+C
    signal.signal(signal.SIGINT, interrupt_handler)

    # load config.json
    with open("config.json", "r") as f:
        config = json.load(f)
    # initialize the values
    startUrls = config["startUrls"]
    untrackedDomains = config["untrackedDomains"]
    maxDepth = config["maxDepth"]

    # Convert startUrls from str's Vertex's
    startingNodes = []
    for url in startUrls:
        startingNodes.append(gh.Vertex(url, G))

    # handle runtime options
    spiderOpt = int(input("""What would you like to do?
    (1) Start the Spider
    (2) Resume the spider
    (3) Load the most recent graph and analyze it
> """))

    analysisOpt = int(input("""Analyze which graphs?
    (1) Page Graph
    (2) Domain Graph
    (3) Both    
    (4) Neither
> """))

    nameDefault = config["nameDefault"]
    nameOpt = input(f"What is this crawl called (or what crawl are we loading)?\n(0)=\033[1;4m{nameDefault}\033[m, (1)=Spider, (2)=Crawl\n> ")
    # handle default value
    if nameOpt == "":
        nameOpt = 0
    nameOpt = int(nameOpt)

    title = [nameDefault, "Spider", "Crawl"][nameOpt]

    # run the spider
    if spiderOpt == 1:
        spiderDFS(startingNodes, 3)
        print("Saving data...")
        G.save(title)
        print("Saved!")
    
    #load from disk
    if spiderOpt == 2 or spiderOpt == 3:
        G.load(title)

    # resume spider
    if spiderOpt == 2:
        pass

    # Save Graph to disk
    if spiderOpt == 1 or spiderOpt == 2:
        pass

    # analysis
    if spiderOpt <= 3:



        timestamp = getTimestamp()
        
        if analysisOpt == 1 or analysisOpt == 3:
            print("PAGE GRAPH")
            G.printGraphSize()

            # Then convert to nx.Graph
            g = gh.graphToNxGraph(G)
            print("DRAWING...")    
            gh.drawGraph(g, f"output/{title}_pageGraph__{timestamp}.jpg")
        
        if analysisOpt == 2 or analysisOpt == 3:
            # Convert page Graph into one representing domains only
            print("DOMAIN GRAPH")
            DomainGraph = gh.graphToDomainGraph(G)
            DomainGraph.printGraphSize()

            # to nx.Graph
            g_domain = gh.graphToNxGraph(DomainGraph)
            print("DRAWING...")
            gh.drawGraph(g_domain, f"output/{title}_domainGraph__{timestamp}.jpg")
