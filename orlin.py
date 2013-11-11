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

def all_balanced(graph):
    """
    Check if all nodes are balanced with respect to node excess values
    """
    for node in graph.nodes_iter():
        if graph.node[node][EXCESS] != 0:
            return False
    return True
def zero_flow(graph):
    """
    Check if all the edges have zero pseudoflow (no flow)
    """
    for source,sink in graph.edges_iter():
        if graph[source][sink][FLOW] != 0:
            return False
    return True
def delta_optimal(graph, delta):
    """
    Check if all the nodes are delta optimal
    """
    for node in graph.nodes_iter():
        if abs(graph.node[node][EXCESS]) >= delta:
            return False
    return True
def do_contraction_if_exist(graph, n, delta, mem_node, mem_edge, cinfo, orig_cost):
    """
    Contraction if neccessary, to improve Edmond-Karp algorithm
    """
    threshold = 4*n*delta #Threshold for pseudoflow check
    flag = False #Flag to indicate contraction has occurred and needs to combine some nodes and edges
    edges_to_remove = []
    edges_to_add = []
    nodes_to_add = []
    for source,sink in graph.edges_iter():
        if graph.has_edge(source, sink):
            if graph[source][sink][FLOW] >= threshold:
                flag = True
                print '--Contraction occurred between %s and %s nodes--%s' % (source,sink, delta)
                b_source,b_sink = graph.node[source][UNITS],graph.node[sink][UNITS] #b(i) and b(j)
                e_source,e_sink = graph.node[source][EXCESS],graph.node[sink][EXCESS] #e(i) and e(j)
                p_source,p_sink = graph.node[source][POTENTIAL],graph.node[sink][POTENTIAL] #PI(i) and PI(j)
                #print '__in_contract_%s and %s' % (e_source,e_sink)
                vnode_name = source + sink + 1000 #Newly created node name
                cinfo[vnode_name] = {'source':(source,e_source), 'sink':(sink,e_sink), COST:orig_cost[(source,sink)]}
                nodes_to_add.append((vnode_name, {UNITS:(b_source+b_sink), POTENTIAL:(p_source+p_sink), EXCESS:(e_source+e_sink)}))
                mem_node[vnode_name] = {UNITS:(b_source+b_sink), POTENTIAL:(p_source+p_sink), EXCESS:(e_source+e_sink)}
                
                for xs,xt in graph.in_edges_iter(source): #For (k,i) arcs
                    if xs != sink:
                        cost = max(0,graph[xs][source][COST])
                        flow = graph[xs][source][FLOW]
                        capacity = graph[xs][source].get(CAPACITY, MAX_INT)
                        edges_to_add.append((xs, vnode_name, {COST:cost, FLOW:flow, CAPACITY:capacity}))
                        if (xs, vnode_name) in orig_cost and (orig_cost.get((xs,source),cost) > orig_cost[(xs, vnode_name)]):
                            pass
                        else:
                            orig_cost[(xs, vnode_name)] = orig_cost.get((xs,source),cost)
                        edges_to_remove.append((xs, source))
                for xs,xt in graph.out_edges_iter(source): #For (i,k) arcs
                    if xt != sink:
                        cost = max(0,graph[source][xt][COST])
                        flow = graph[source][xt][FLOW]
                        capacity = graph[source][xt].get(CAPACITY, MAX_INT)
                        edges_to_add.append((vnode_name, xt, {COST:cost, FLOW:flow, CAPACITY:capacity}))
                        if (vnode_name, xt) in orig_cost and (orig_cost.get((source,xt),cost) > orig_cost[(vnode_name, xt)]):
                            pass
                        else:
                            orig_cost[(vnode_name, xt)] = orig_cost.get((source,xt),cost)
                        edges_to_remove.append((source, xt))
                    
                for xs,xt in graph.in_edges_iter(sink): #For (k,j) arcs
                    if xs != source:
                        cost = max(0,graph[xs][sink][COST])
                        flow = graph[xs][sink][FLOW]
                        capacity = graph[xs][sink].get(CAPACITY, MAX_INT)
                        edges_to_add.append((xs, vnode_name, {COST:cost, FLOW:flow, CAPACITY:capacity}))
                        if (xs, vnode_name) in orig_cost and (orig_cost.get((xs, sink),cost) > orig_cost[(xs, vnode_name)]):
                            pass
                        else:
                            orig_cost[(xs, vnode_name)] = orig_cost.get((xs,sink),cost)
                        edges_to_remove.append((xs, sink))
                for xs,xt in graph.out_edges_iter(sink): #For (j,k) arcs
                    if xt != source:
                        cost = max(0,graph[sink][xt][COST])
                        flow = graph[sink][xt][FLOW]
                        capacity = graph[sink][xt].get(CAPACITY, MAX_INT)
                        edges_to_add.append((vnode_name, xt, {COST:cost, FLOW:flow, CAPACITY:capacity}))
                        if (vnode_name, xt) in orig_cost and (orig_cost.get((sink,xt),cost) > orig_cost[(vnode_name, xt)]):
                            pass
                        else:
                            orig_cost[(vnode_name, xt)] = orig_cost.get((sink,xt),cost)
                        edges_to_remove.append((sink, xt))
                
                edges_to_remove.append((source, sink))
                graph.remove_nodes_from([source,sink])
    if flag: #If contraction has occurred in the check above
        graph.remove_edges_from(edges_to_remove)
        graph.add_nodes_from(nodes_to_add)
        for src,snk,dct in edges_to_add:
            mem_edge[src] = {snk:dct}
            if graph.has_edge(src, snk):
                ce = graph[src][snk]
                if dct[COST] < ce[COST]:
                    graph.add_edge(src, snk, dct)
            else:
                graph.add_edge(src, snk, dct)
    return flag
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
def get_half_delta_source_nodes(graph, delta):
    """
    Get all the source nodes, determined by the half delta value and unit amount
    """
    lst = []
    for node in graph.nodes_iter():
        if graph.node[node][EXCESS] >= (delta/2) and graph.node[node][UNITS] < 0:
            lst.append(node)
    return lst
def get_half_delta_sink_nodes(graph, delta):
    """
    Get all the sink nodes, determined by the half delta value and unit amount
    """
    lst = []
    for node in graph.nodes_iter():
        if graph.node[node][EXCESS] <= -(delta/2) and graph.node[node][UNITS] > 0:
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
            print('(%s(%s), %s, %.2f)' % (n,graph.node[n][attr_nodelbl],nbr,data))

def arcs_expansion_and_cost_cal(contraction_info, ocost):
    """
    Once the algorithm terminates, expansion is performed and final cost is calculated in the process
    """

    if len(contraction_info)>0:
        print ''
        print 'Expanding the contracted node and cost calculation of flows from contracted nodes'
    global _cost
    klist = contraction_info.keys()
    klist = sorted(klist)
    klist.reverse()
    #print klist
    pout = -30
    i = 0
    internal = True
    for k in klist:
        #print ('---in--')
        v  = contraction_info[k]
        units = v['source'][1]
        
        if i==0:
            _cost += units*ocost[(v['source'][0], v['sink'][0])]
            display = (k,units,v['source'][0],v['sink'][0],ocost[(v['source'][0], v['sink'][0])])
            print 'ContactedNode(%s): There is additional flows of "%s" from %s to %s with the cost of %.2f' % display
        if internal and i>0:
            _cost += units*ocost[(v['source'][0], v['sink'][0])]
            display = (k,units,v['source'][0],v['sink'][0],ocost[(v['source'][0], v['sink'][0])])
            print 'ContactedNode(%s): There is additional flows of "%s" from %s to %s with the cost of %.2f' % display
        elif not internal and v['sink'][1]<0:
            units = abs(v['sink'][1])
            _cost += units*ocost[(v['source'][0], v['sink'][0])]
            display = (k,units,v['source'][0],v['sink'][0],ocost[(v['source'][0], v['sink'][0])])
            print 'ContactedNode(%s): There is additional flows of "%s" from %s to %s with the cost of %.2f' % display
            
        previous = contraction_info.get(v['source'][0],None)
        if previous:
            
            if (previous['source'][0], v['sink'][0]) in ocost and (previous['sink'][0], v['sink'][0]) in ocost:
                if ocost[(previous['source'][0], v['sink'][0])]>ocost[(previous['sink'][0], v['sink'][0])]:
                    internal = True
                else:
                    internal = False
            else:
                if (previous['source'][0], v['sink'][0]) not in ocost:
                    internal = True
                elif (previous['sink'][0], v['sink'][0]) not in ocost:
                    internal = False
        
        i += 1

def orlin_scaling(graph):
    """
    Edmond-Karp scaling algorithm implementation
    """
    global _cost
    mem_n = {}
    mem_e = {}
    #Initialization of x, PI, e, U and delta
    egraph = graph.copy()
    n = egraph.number_of_nodes()
    contraction_info = {}
    ocost = {}
    for es,et in egraph.edges_iter():
        ocost[(es,et)] = egraph[es][et][COST]
    max_unit = -MAX_INT #maximum node weight
    for node in egraph.nodes_iter():
        egraph.node[node][EXCESS] = egraph.node[node][UNITS]
        egraph.node[node][POTENTIAL] = 0
        if max_unit < egraph.node[node][UNITS]:
            max_unit = egraph.node[node][UNITS] #maximum node weight
    for source,sink in egraph.edges_iter():
        egraph[source][sink][FLOW] = 0 #No pseudoflow in the beginning
        egraph[source][sink][CAPACITY] = MAX_INT #Uncapicitated problem (i.e.Inifinite capacity)
    delta = max_unit
    
    #Delta scaling phase begins
    while delta > 0 and not all_balanced(egraph):
        #delta value verification and if neccessary change the delta value
        if zero_flow(egraph) and delta_optimal(egraph, delta):
            max_unit = -MAX_INT
            for node in egraph.nodes_iter():
                if max_unit < egraph.node[node][UNITS]:
                    max_unit = egraph.node[node][UNITS]
            delta = max_unit

        
        #Check if contraction requires or not, and do the contraction if appropriate
        while do_contraction_if_exist(egraph, n, delta, mem_n, mem_e, contraction_info, ocost):
            pass
        print 'INFO: --delta scaling phase with delta value = %s--' % delta
        S = get_delta_source_nodes(egraph, delta) #Source nodes
        T = get_delta_sink_nodes(egraph, delta) #Sink nodes
        #Update source and sink nodes by considering additional information
        hsr_nodes = get_half_delta_source_nodes(egraph, delta)
        hsnk_nodes = get_half_delta_sink_nodes(egraph, delta)
        rS,rT = set(S),set(T)
        rS_prime,rT_prime = set(hsr_nodes),set(hsnk_nodes)
        rS = rS.union(rS_prime)
        rT = rT.union(rT_prime)

        S = list(rS) 
        T = list(rT)
        
        while len(S) > 0 and len(T) > 0:

            #Randomly choose one source and one sink
            k = S[random.randint(0, len(S)-1)]
            l = T[random.randint(0, len(T)-1)]

            #Finding shortest paths by means of Bellman-Ford algorithm
            try:
                p,d =nx.bellman_ford(egraph, k, weight=COST)
            except:
                display_graph_info(egraph, EXCESS, COST)
                #print k
                #print l
                sys.exit()
            for node in egraph.nodes_iter():
                egraph.node[node][POTENTIAL] -= d.get(node, 0)

            #Flow delta unit from k to l, update reverse flow information if appropriate
            temp = []
            temp.append(l)
            #print str(k)+'+++'+str(l)
            predecessor_node = p[l]
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
                    if src in contraction_info:
                        contraction_info[src]['source'] = (contraction_info[src]['source'][0],contraction_info[src]['source'][1]-delta)
                    if (src,snk) in ocost:
                        _cost += ocost[(src,snk)]*delta
                    else:
                        try:
                            _cost += graph[src][snk][COST]*delta
                        except KeyError:
                            _cost -= graph[snk][src][COST]*delta
                            pass
                    #Reverse flow (capacity and cost update)
                    if not egraph.has_edge(snk,src):
                        egraph.add_edge(snk,src,{FLOW:0,CAPACITY:delta, COST:-egraph[src][snk][COST]})
                    else:
                        egraph[snk][src][CAPACITY] += delta

            #Update node excesses
            for node in egraph.nodes_iter():
                if node in mem_n:
                    egraph.node[node][EXCESS] = mem_n[node][UNITS] + egraph.in_degree(node, weight=FLOW) - egraph.out_degree(node, weight=FLOW)
                else:
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
    #print _cost
    #print ocost
    #print contraction_info
    arcs_expansion_and_cost_cal(contraction_info, ocost) #Cost calculation and expansion of contracted nodes

def main():
    fn = raw_input('Input filename:')
    try:
        dgraph = get_graph_from_input(fn)
        orlin_scaling(dgraph)
        print 'Total cost: %s' % _cost
    except IOError:
        print 'File not found.'

if __name__ == '__main__':
    main()
