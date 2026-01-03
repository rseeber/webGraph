import requests
from bs4 import BeautifulSoup
import time
import urllib.robotparser as rp
import json

# returns (domain, resource) as a 2-tuple of a URL. Does not verify input.
def splitURL(link, getDomain=""):
    # find the first "/" AFTER the "https://"
    split = link.find("/", 8)
    # everything after the "/"
    resource = link[split+1:]
    # everything between "https://" and "/"
    domain = link[8:split]

    return domain, resource

# Returns Second-Level Domain of a provided domain
# 
def splitDomain(domain):
    return domain.split(".")

# fix local links, remove queries, end with a "/"
def standardizeLink(link, getDomain):
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
    
    return link

def parseWebpage(pageURL):
    getDomain, getResource = splitURL(pageURL)
    reqs = requests.get(pageURL, headers=requestHeaders)
    soup = BeautifulSoup(reqs.text, 'html.parser')

    inlinks = []
    outlinks = []
    outdomains = []
    # iterate through each <a> tag
    for a in soup.find_all('a'):
        # get the link
        link = a.get('href')
        # ignore broken or missing links
        if link == None:
            continue
        # standardize it
        link = standardizeLink(link, getDomain) 

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
    except:
        edges[myEdge] = 1

# deprecated
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
            if u in domain:
                track = False
        # otherwise, add it
        if(track):
            urls.add(link)

# returns True if the url is allowed to be scraped
def robotsCheck(url):
    domain, resource = splitURL
    rfp = rp.RobotFileParser()
    rfp.set_url(domain+"/robots.txt")
    rfp.read()

    delay = rfp.crawl_delay(requestHeaders["User-Agent"])

    allowed = rfp.can_fetch(requestHeaders["User-Agent"], url)

    if allowed == None:
        allowed = rfp.can_fetch("*", url)
    
    return allowed, delay


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
def spider(startUrls, N, untrackedDomains, data={}, i=0):

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

        data = (linkDict, linkProgressDict, urlIndex)

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

    # iterate through the provided pages
    for url in startUrls:
        # check robots.txt




        

        print("waiting 5 seconds before fetching resource "+url)
        time.sleep(1)
        # Parse the page
        inlinks, outlinks, outdomains = parseWebpage(url)

        linkDict.update({url: inlinks+outlinks})
        linkProgressDict.update({url:0})

        countUrls(inlinks+outlinks, urls)

        urlIndex.update(urls)

        # fill out urls, edges, and domainEdges with data from the parsed page
        #buildGraph(inlinks + outlinks, url, urls, edges, domainEdges)

        # display some data for the user
        print("urls found: "+str(urls))
        print("url count = "+str(len(urls)))

    # Update the data object
    ## Note: since this is to be a list of lists, append() is correct (don't use extend()!!)
    #data[2].update(urls)
    ## Add the edges
    #data["edges"].update(edges)
    #data["domainEdges"].update(domainEdges)

    # recursion call
    print("REPEAT SPIDER CALL ON "+str(urls))
    return spider(urls, N-1, untrackedDomains, data, i+1)

robotsTxt = {}
requestHeaders = {"User-Agent":"WebGraphUtility", "From":"riverseeber12@gmail.com"}


if __name__ == "__main__":
    #urls = ["https://pluralistic.net/"]
    startUrls = ["https://pluralistic.net/2025/12/08/giant-teddybears/"]
    untrackedDomains = ["google.com", "x.com", "twitter.com", "reddit.com"]

    data = spider(startUrls, 2, untrackedDomains)

    f = open("output/data.json", "w")
    f.write(repr(data))


    #f = open("output/data.json", "w")
    #f.write(myJson)