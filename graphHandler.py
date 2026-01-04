import networkx as nx
import matplotlib.pyplot as plt
import random


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
    def get(self, element):
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
          

    def addEdge(self, myEdge):
        # look for if the edge already exists
        for e in self.E:
            # if it does, increment the weight
            if e.u == myEdge.u and e.v == myEdge.v:
                e.weight += 1
                return
        # otherwise, add it to the list
        self.E.append(myEdge)

    # Function overload that takes urls instead of an Edge object
    def addEdge_url(self, u_url, v_url):
        myEdge = Edge(Vertex(u_url), Vertex(v_url))
        self.addEdge(myEdge)

    def printGraphSize(self):
        print(f"Graph Size:\n\tNodes: {len(self.V)}\n\tEdges: {len(self.E)}")


class Vertex:
    def __init__(self, url, G=None, GD=None):
        self.__adjacent = None
        self.__adjacentDomains = None
        self.G = G
        self.GD = GD    # Domain Graph
        self.color = "white"
        self.url = url
    
    def __hash__(self):
        return hash(self.url)

    def __str__(self):
        return self.url
        

    def getAdjacent(self):
        # If we haven't fetched the webpage and indexed URLs yet, do that.
        if self.__adjacent == None:
            self.__fetchPage()
        return self.__adjacent

    def getAdjacentDomains(self):
        # If we haven't fetched the webpage and indexed URLs yet, do that.
        if self.__adjacentDomains == None:
            self.__fetchPage()
        return self.__adjacentDomains
    
    def __fetchPage(self):
        import scrape

        # Fetch webpage
        inlinks, outlinks, outdomains = scrape.parseWebpage(self.url)


        # adjacent nodes
        self.__adjacent = []

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


        # adjacent domains (for the domain graph)
        self.__adjacentDomains = []
        for domain in outdomains:
            # This is some pretty godawful code, sorry

            # See if the Domain Graph has this domain yet
            # If it already exists, add the existing node to __adjacentDomains.
            # Otherwise, create a new node.
            #
            # If GD is unset, just create a new node and don't check for uniqueness
            try:
                v = self.GD.get(domain)
            except Exception:
                v = None
            # If this url doesn't have a node yet, create one
            if v == None:
                v = Vertex(domain, self.GD)
            # Then add the node to the list of adjacent nodes
            self.__adjacentDomains.append(v)

# an edge pointing from u to v. Weight is a unit value (1) by default
class Edge:
    def __init__(self, u: Vertex, v:Vertex, weight=1):
        self.u = u
        self.v = v
        self.weight = weight
    def __hash__(self):
        return hash(str(hash(self.u)) + str(hash(self.v)))



# Funcs

# Draw the graph, with the labels raised slightly above the nodes
def drawGraph(G: nx.DiGraph, output):
    plt.figure(figsize=(50, 50))
    pos_nodes = nx.spring_layout(G, weight="weight")
    #pos_nodes = nx.spectral_layout(G)
    #pos_nodes = nx.shell_layout(G)
    #pos_nodes = nx.spectral_layout(G)
    #pos_nodes = nx.community.louvain_communities(G)
    
    #nx.draw_networkx_nodes(G, pos_nodes, node_size=30)
    #nx.draw_networkx_edges(G, pos_nodes, width=0.1, alpha=0.5)
    nx.draw(G, pos_nodes, node_size=50, width=0.1)

    pos_attrs = {}
    for node, coords in pos_nodes.items():
        pos_attrs[node] = (coords[0], coords[1] + 0.02)

    node_attrs = nx.get_node_attributes(G, 'type')
    custom_node_attrs = {}
    for node, attr in node_attrs.items():
        custom_node_attrs[node] = attr

    nx.draw_networkx_labels(G, pos_attrs, font_size=8)

    #plt.margins(x=0.5, y=1.0)
    plt.savefig(output)

def drawGraph_simple(G: nx.DiGraph, output):
    nx.draw_networkx(G, with_labels=False)
    plt.savefig(output)

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


    # Then convert to nx.Graph
    g = nx.DiGraph()

    """
    g.add_node("wikipedia.org")
    g.add_node("google.com")
    g.add_node("techdirt.com")

    # Add edges
    g.add_edge("wikipedia.org", "google.com")

    """
    # Add the nodes/vertices
    for v in G.V:
        g.add_node(v)

    # Add the edges
    for e in G.E:
        g.add_edge(e.u, e.v, weight=e.weight)
        

    # Draw it
    drawGraph_simple(g)
