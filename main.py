import networkx as nx
import matplotlib.pyplot as plt

# Draw the graph, with the labels raised slightly above the nodes
def drawGraph():
    plt.figure()
    pos_nodes = nx.spring_layout(G)
    nx.draw(G, pos_nodes, with_labels=False)

    pos_attrs = {}
    for node, coords in pos_nodes.items():
        pos_attrs[node] = (coords[0], coords[1] + 0.20)

    node_attrs = nx.get_node_attributes(G, 'type')
    custom_node_attrs = {}
    for node, attr in node_attrs.items():
        custom_node_attrs[node] = attr

    nx.draw_networkx_labels(G, pos_attrs)

    plt.margins(x=0.5, y=1.0)
    plt.savefig("output/graph.png")


if __name__ == "__main__":
    # Create an empty graph
    G = nx.Graph()

    # Add nodes
    G.add_node("wikipedia.org")
    G.add_node("google.com")
    G.add_node("techdirt.com")

    # Draw it
    drawGraph()