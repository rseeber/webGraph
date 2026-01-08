import networkx as nx
import matplotlib.pyplot as plt
import random
import pickle
import shutil
import json

# Classes

class Graph:
    def __init__(self):
        self.V = []
        self.E = []

    # checks if a given VERTEX is part of the Graph
    def __contains__(self, element):
        # Vertex
        # if it's a string, create a new vertex with that url value
        if type(element) == str:
            element = Vertex(element)
        
        if type(element) == Vertex:
            #iterate through all elements in V. If one of the elements shares a url, it contains it
            for v in self.V:
                if v.url == element.url:
                    return True
            # otherwise, it does not contain it
            return False

    # Returns a vertex with the same url as the element, or else returns None
    def getVertex(self, element):
        # Vertex
        # if it's a string, create a new vertex with that url value
        if type(element) == str:
            element = Vertex(element)
        
        if type(element) == Vertex:
            #iterate through all elements in V. If one of the elements shares a url, it contains it
            for v in self.V:
                if v.url == element.url:
                    return v
            # otherwise, it does not contain it
            return None
    
    # add a Vertex with the given url, unless it already exists
    def addVertex_url(self, url, dist=None):
        for u in self.V:
            # if the vertex is already there
            if u.url == url:
                # update the dist if a shorter path was found
                if dist != None and dist < u.dist:
                    u.dist = dist
                return
        # if it's new, add it
        self.V.append(Vertex(url, G))

    # adds the edge if it doesn't exist, or else increments the weight
    # if you specify addWeight, it can add the same edge that many times
    # ex: addWeight=7 means add that edge 7 times, instead of having to
    # call the function multiple times
    def addEdge(self, myEdge, addWeight=1):
        # look for if the edge already exists
        for e in self.E:
            # if it does, increment the weight
            if e.u == myEdge.u and e.v == myEdge.v:
                e.weight += addWeight
                return
        # otherwise, add it to the list
        self.E.append(myEdge)

    # Function overload that takes urls instead of an Edge object
    # adds the edge if it doesn't exist, or else increments the weight
    def addEdge_url(self, u_url, v_url, addWeight=1):
        myEdge = Edge(Vertex(u_url), Vertex(v_url))
        self.addEdge(myEdge, addWeight)

    def printGraphSize(self):
        print(f"Graph Size:\n\tNodes: {len(self.V)}\n\tEdges: {len(self.E)}")


    def exportJson(self):
        # Saves the Graph data structure to a Python Dict ("json")
        # This is just so we can write to disk. 
        # In order to handle the data, we must import the Json again so lookups are possible
        myJson = {
            "V": [],
            "V_props": [],  #ex: [{"color": "black"}, ...]
            # Note: the adjacent property is stored in the edges, so doesn't need to be
            # stored in V_props

            # We're using an adjacency list for this storage method.
            # See "Introdction to Algorithms 3e" by Cormen pg 590 (Ch 22) for more
            "E": {}, #ex: {"a": ["j", "k", "l"], "b": ["x", "y", "z"], ...}
            # props are matched to index:   "a, j"      "a, k"          "a, l"              "b, x"
            "E_props": {} #ex: {"a": [{"weight": 5}, {"weight": 7}, {"weight": 1}], "b": [{"weight": 2}, ...], ...}
            # Notice that all keys are hashable (strings), even though the values are more complex.
            # this makes lookups easy and possible.
        }
        # Index the nodes
        for v in self.V:
            # append the url/title of the node to the list of nodes
            myJson["V"].append(v.url)
            # append the property dictionary to the list of node properties
            props = {"color": v.color, "dist": v.dist}
            myJson["V_props"].append(props)

            # create an empty entry for the node in the edge and edge prop lists
            myJson["E"].update({v.url: []})
            myJson["E_props"].update({v.url: []})

        
        # Index the edges
        for e in self.E:
            # add the edges
            myJson["E"][e.u.url].append(e.v.url)
            # add the edge properties
            myJson["E_props"][e.u.url].append({"weight": e.weight})

        return myJson

    # Load data with the given title into the Graph
    def load(self, title):
        with open(f"output/{title}.json") as f:
            myJson = json.load(f)
            self.loadFromJson(myJson)

    # given a json-like python dict, load the data into the Graph
    def loadFromJson(self, myJson):
        if type(myJson) != dict:
            print("ERROR: loadFromJson() requires a python dict as input, not "+type(myJson))
            return
        # iterate through list of nodes
        for i in range(len(myJson["V"])):
            # grab the url at index i
            url = myJson["V"][i]
            # create a vertex with that url, setting the current graph as the graph
            u = Vertex(url, self)
            # PROPERTIES
            # set the color from "color" at index i in V_props
            u.color = myJson["V_props"][i]["color"]

            # distance from starting node(s)
            u.dist = myJson["V_props"][i]["dist"]

            # add the adjacent property
            edges = myJson["E"][url] # list
            u.setAdjacent(edges)

            # save the edge to the graph
            self.V.append(u)

            # iterate through the adjacency list for u
            for j in range(len(edges)):
                v_url = edges[j]
                # get the weight
                edgeWeight = myJson["E_props"][url][j]["weight"]
                # create the Edge object
                # Notice that we're creating the edge using urls (str) not Vertex
                #myEdge = Edge(u.url, v_url, weight=edgeWeight)

                # add the edge to the Graph
                self.addEdge_url(u.url, v_url, edgeWeight)

                #self.E.append(myEdge)
            
    # save current Graph data to a json file, filename starting with title
    def save(self, title):
        import scrape
        myJson = self.exportJson()
        with open(f"output/{title}.json", "w") as f:
            json.dump(myJson, f, indent=4)

class Vertex:
    def __init__(self, url, G=None, GD=None):
        self.__adjacent = None
        self.__adjacentDomains = None
        self.dist = None
        self.G = G
        self.color = "white"
        self.url = url
    
    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return self.url

    # equality is based on if they have the same url
    def __eq__(self, v):
        if type(v) == Vertex:
            return self.url == v.url
        return False
        
    def setAdjacent(self, urls: list):
        # In case this ever gets called when it shouldn't be
        if self.__adjacent != None:
            print("Vertex.setAdjacent(): WARNING: non-empty contents of __adjacent being overwritten! len = "+len(self.__adjacent))
        
        # wipe the list
        self.__adjacent = []

        # iterate through each item in the list, append it to __adjacent
        for url in urls:
            self.__adjacent.append(url)

    # Returns True if we've already fetched the webpage for this node
    def isAdjacentCached(self):
        return self.__adjacent != None

    def getAdjacent(self):
        # If we haven't fetched the webpage and indexed URLs yet, do that.
        if self.__adjacent == None:
            self.__fetchPage()
        return self.__adjacent

    def __fetchPage(self):
        import scrape

        # adjacent nodes
        self.__adjacent = []

        # Fetch webpage
        if scrape.robotsCheck(self.url):
            inlinks, outlinks, outdomains = scrape.parseWebpage(self.url)
        else:
            return

        # temporary index we use to improve Big O speed for
        # checking if a url has already been added.
        urlsAdded = []

        for url in inlinks+outlinks:
            # If this url doesn't have a node yet, create one
            v = self.G.get(url)
            if v == None:
                v = Vertex(url, self.G)

                # if the url is already in __adjacent, just skip it
                # (no need to add twice)
                if v.url in urlsAdded:
                    continue
                
            # Then add the node to the list of adjacent nodes
            self.__adjacent.append(v)
            # keep track of which urls we've added to __adjacent
            # so the search complexity is easier for avoiding duplicates
            urlsAdded.append(v.url)



# an edge pointing from u to v. Weight is a unit value (1) by default
# while technically u and v are supposed to be Vertex type, you can also
# pass in just a string (url/title), and everything still works
class Edge:
    def __init__(self, u: Vertex, v:Vertex, weight=1):
        self.u = u
        self.v = v
        self.weight = weight
    def __hash__(self):
        return hash(str(hash(self.u)) + str(hash(self.v)))


# Convert a gh.Graph to nx.Graph
def graphToNxGraph(G: Graph):
    g = nx.DiGraph()

    # Add the nodes/vertices
    for v in G.V:
        g.add_node(v)

    # Add the edges
    for e in G.E:
        g.add_edge(e.u, e.v, weight=e.weight)
    
    return g

def graphToDomainGraph(G: Graph):
    GG_domain = Graph()

    # go through each vertex in the original graph
    for v in G.V:
        # grab the domain only
        domain = scrape.splitURL(v.url)[0]
        # if the domain is not already in the list, add it
        if GG_domain.getVertex(domain) == None:
            GG_domain.V.append(Vertex(domain))
    
    # go through the edges
    for e in G.E:
        # grab the domain of u
        u_domain = scrape.splitURL(e.u.url)[0]
        # grab the domain of v
        v_domain = scrape.splitURL(e.v.url)[0]

        # add the edge (this func increments weight if it already exists)
        GG_domain.addEdge_url(u_domain, v_domain)

    return GG_domain

# Funcs

# Draw the graph, with the labels raised slightly above the nodes
def drawGraph(G: nx.DiGraph, output):
    plt.figure(figsize=(100, 75))
    pos_nodes = nx.spring_layout(G, weight="weight", k=None)
    #pos_nodes = nx.spectral_layout(G)
    #pos_nodes = nx.shell_layout(G)
    #pos_nodes = nx.spectral_layout(G)
    #pos_nodes = nx.community.louvain_communities(G)
    
    #nx.draw_networkx_nodes(G, pos_nodes, node_size=30)
    #nx.draw_networkx_edges(G, pos_nodes, width=0.1, alpha=0.5)
    nx.draw(G, pos_nodes, node_size=200, width=0.1)

    pos_attrs = {}
    for node, coords in pos_nodes.items():
        pos_attrs[node] = (coords[0], coords[1] + 0.004)

    node_attrs = nx.get_node_attributes(G, 'type')
    custom_node_attrs = {}
    for node, attr in node_attrs.items():
        custom_node_attrs[node] = attr

    nx.draw_networkx_labels(G, pos_attrs, font_size=16)

    #plt.margins(x=0.5, y=1.0)
    plt.savefig(output)

def drawGraph_simple(G: nx.DiGraph, output):
    nx.draw_networkx(G, with_labels=False)
    plt.savefig(output)


# Main()

if __name__ == "__main__":
    # Create an empty graph
    G = Graph()

    n = 50
    # Create nodes
    for i in range(n):
        node = Vertex(f"{i}")
        G.V.append(node)

    # Create edges
    for i in range(n):
        for j in range(n):
            if random.randint(0, 100) < 25:
                G.E.append(Edge(G.V[i], G.V[j]))

    import scrape

    # Then convert to nx.Graph
    g = scrape.graphToNxGraph(G)
    
    drawGraph(g, "output/testGraph.jpg")
