class Graph:
    class Node:
        def __init__(self, name, color=None, weight=None):
            self.name = name
            self.color = color
            self.weight = weight
        def __hash__(self):
            return hash(self.name)
    
    def __init__(self):
        # Nodes
        self.nodes = [] # a list of Node objects

        # Edges
        self.edges = {} # e.g. {node1 : [nodeA, nodeB, ...], node2 : [...], ...}

    # adds a node if it does not already exist
    def addNode(self, v: Node):
        if v in self.nodes:
            return
        else:
            # add it to the list of nodes
            self.nodes.append(v)
            # add the nodeProps
            self.nodeProps.update()
            # add an entry to the edges list (no edges yet)
            self.edges.update({v:[]})

    def addEdge(self, u: Node, v: Node):
        # If the edge is not in the adjacency list, add it (with weight 1)
        if v not in self.edges[u]:
            v.weight = 1
            self.edges[u].append(v)
        # If it does, find it, and increment the weight
        else:
            for x in self.edges[u]:
                if x.name == v.name:
                    x.weight += 1

    def setNodeColor(self, u: Node, color: str):
        # find the node with the same color
        for x in self.nodes:
            # when found, set the color
            if x.name == u.name:
                x.color = color
    
    def getNodeColor(self, u: Node):
        for x in self.nodes:
            if x.name == u.name:
                return x.color
    
    # returns a LIST of strings, corresponding to the names of adjacent nodes
    def getNodeAdj(self, u: Node):
        # if self.edges[u.name] == None
        # go fetch that shit and cache the data
        return self.edges[u.name]



x = Graph.Node(1)
G = Graph()
G.addNode(x)