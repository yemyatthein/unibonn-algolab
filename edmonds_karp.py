import networkx as nx
from numpy import log2
import random
import sys

MAX_INT = sys.maxint

UNITS = 'units_available'
COST = 'cost_of_flow'
EXCESS = 'excess'
POTENTIAL = 'node_potential'
FLOW = 'pseudoflow'
CAPACITY = 'capacity'

_cost = 0

def get_graph_from_input(input_filename):
    """
    Get the graph data from input file
    """
    f = open(input_filename, 'r')
    lines  = f.readlines()
    f.close()
    node_remember = set()
    nodes = []
    edges = []
    for line in lines:
        if line.startswith('##') or not line.strip():
            continue
        parts = line.split(',')
        source_info = parts[0].split('|')
        dest_info = parts[1].split('|')
        source_node = int(source_info[0])
        source_amount = int(source_info[1])
        dest_node = int(dest_info[0])
        dest_amount = int(dest_info[1])
        cost = int(parts[2])
        if source_node not in node_remember:
            nodes.append((source_node, {UNITS:source_amount}))
            node_remember.add(source_node)
        if dest_node not in node_remember:
            nodes.append((dest_node, {UNITS:dest_amount}))
            node_remember.add(dest_node)        
        edges.append((source_node, dest_node, {COST:cost}))
    dgraph = nx.DiGraph()
    dgraph.add_nodes_from(nodes)
    dgraph.add_edges_from(edges)
    return dgraph

def calculate_cost(graph, og):
    global _cost
    for source,sink in graph.edges_iter():
        try:
            _cost += og[source][sink][COST]*graph[source][sink][FLOW]
            print str(source) + '->' + str(sink) + '->' + str(graph[source][sink][FLOW])
        except KeyError:
            _cost -= og[sink][source][COST]*graph[source][sink][FLOW]
            #print str(source) + '->' + str(sink) + '->' + str(graph[source][sink][FLOW])
            continue

def all_balanced(graph):
    """
    Check if all nodes are balanced with respect to node excess values
    """
    for node in graph.nodes_iter():
        if graph.node[node][EXCESS] != 0:
            return False
    return True
def get_delta_source_nodes(graph, delta):
    """
    Get all the source nodes, determined by the delta value
    """
    lst = []
    for node in graph.nodes_iter():
        if graph.node[node][EXCESS] >= delta:
            lst.append(node)
    return lst
def get_delta_sink_nodes(graph, delta):
    """
    Get all the sink nodes, determined by the delta value
    """
    lst = []
    for node in graph.nodes_iter():
        if graph.node[node][EXCESS] <= -delta:
            lst.append(node)
    return lst
def display_graph_info(graph, attr_nodelbl, attr_edgelb):
    """
    Print the information of nodes and edges (debugging purpose)
    @param attr_nodelbl - Labels for nodes of the graph (Must be valid attribute name of the node)
    @param attr_edgelbl - Labels for edges of the graph (Must be valid attribute name of the edge)
    """
    for n,nbrs in graph.adjacency_iter():
        for nbr,eattr in nbrs.items():
            data = eattr[attr_edgelb]
            print('(%d(%d), %d, %.3f)' % (n,graph.node[n][attr_nodelbl],nbr,data))

def rhs_scaling(graph):
    """
    Edmond-Karp scaling algorithm implementation
    """

    #Initialization of x, PI, e, U and delta
    egraph = graph.copy()
    max_unit = -MAX_INT #maximum node weight 
    for node in egraph.nodes_iter():
        egraph.node[node][EXCESS] = egraph.node[node][UNITS]
        egraph.node[node][POTENTIAL] = 0
        if max_unit < egraph.node[node][UNITS]:
            max_unit = egraph.node[node][UNITS] #maximum node weight
    for source,sink in egraph.edges_iter():
        egraph[source][sink][FLOW] = 0 #No pseudoflow in the beginning
        egraph[source][sink][CAPACITY] = MAX_INT #Uncapicitated problem (i.e.Inifinite capacity)
    U = 1 + max_unit
    
    #delta = int(pow(2,(float(log2(U))-1))) #Initial delta value (Original given in paper)

    #Customized/Modified delta value (initial value)
    delta = 1
    while delta < U:
        delta *= 2
    delta  /= 2

    #Delta scaling phase begins
    while delta > 0 and not all_balanced(egraph):
        print 'INFO: --delta scaling phase with delta value = %s--' % delta
        S = get_delta_source_nodes(egraph, delta) #Source nodes
        T = get_delta_sink_nodes(egraph, delta) #Sink nodes
        
        while len(S) > 0 and len(T) > 0:

            #Randomly choose one source and one sink
            k = S[random.randint(0, len(S)-1)]
            l = T[random.randint(0, len(T)-1)]

            #Finding shortest paths by means of Bellman-Ford algorithm
            p,d =nx.bellman_ford(egraph, k, weight=COST)

            #Update node potentials
            for node in egraph.nodes_iter():
                egraph.node[node][POTENTIAL] -= d.get(node, 0)

            #Flow delta unit from k to l, update reverse flow information if appropriate
            temp = []
            temp.append(l)
            predecessor_node = p[l]
            #print str(k) + '-to-' +str(predecessor_node)
            while predecessor_node != k:
                temp.append(predecessor_node)
                predecessor_node = p[predecessor_node]
            temp.append(k)
            temp.reverse()
            for i in xrange(1, len(temp)):
                src = temp[i-1]
                snk = temp[i]
                if egraph[src][snk][CAPACITY] > (egraph[src][snk][FLOW]+delta):
                    egraph[src][snk][FLOW] += delta
                    print 'INFO: Flow from %s to %s % unit(s)' % (src, snk, delta)
                    #Reverse flow (capacity and cost update)
                    if not egraph.has_edge(snk,src):
                        egraph.add_edge(snk,src,{FLOW:0,CAPACITY:delta, COST:-egraph[src][snk][COST]})
                    else:
                        egraph[source][sink][CAPACITY] += delta

            #Update node excesses
            for node in egraph.nodes_iter():
                egraph.node[node][EXCESS] = graph.node[node][UNITS] + egraph.in_degree(node, weight=FLOW) - egraph.out_degree(node, weight=FLOW)

            #Update reduced costs
            for source,sink in egraph.edges_iter():
                egraph[source][sink][COST] = egraph[source][sink][COST] - egraph.node[source][POTENTIAL] + egraph.node[sink][POTENTIAL]

            #Update Source and Sink node sets
            S = get_delta_source_nodes(egraph, delta)
            T = get_delta_sink_nodes(egraph, delta)

        #Update delta
        delta /= 2

    print ''
    print 'Displaying the resulting graph after flows.'
    display_graph_info(egraph,EXCESS,FLOW) #Display for debug
    calculate_cost(egraph, graph)

def main():
    fn = raw_input('Input filename:')
    try:
        dgraph = get_graph_from_input(fn)
        rhs_scaling(dgraph)
        print ''
        print 'Total Cost: ' + str(_cost)
    except IOError:
        print 'File not found.'

if __name__ == '__main__':
    main()
