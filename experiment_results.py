import json
import itertools
import re
import matplotlib.pyplot as plt

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b) 

def get_throughput(filename):
    with open (filename, 'r') as fp:
        lastLine = fp.readlines()[-1]
        regex = "\[.+\] *(\d\.\d)- *(\d\.\d*) *sec *(\d+\.?\d*) *(KBytes|MBytes) *(\d+\.?\d*) *(Mbits/sec|Kbits/sec)"
        match = re.search(regex, lastLine)
        if match:
            start_time = float(match.group(1))
            end_time = float(match.group(2))
            total_time = end_time - start_time
            nbytes_transferred = float(match.group(3))
            transfer_units = match.group(4)
            bandwidth = float(match.group(5))
            bandwidth_units = match.group(6)
            
            # convert to mbits if necessary
            if transfer_units == "KBytes":
                nbytes_transferred *= 0.008
            elif transfer_units == "MBytes":
                nbytes_transferred *= 8
            if bandwidth_units == "Kbits/sec":
                bandwidth *= 0.001

            #return (nbytes_transferred/total_time)/bandwidth
            return bandwidth

        else:
            print 'could not parse file %s' % filename

def get_average_throughput_per_pair(client, server, test_type):
     # from the jellyfish paper, results are averaged over 5 runs
    host_pair_sum = 0
    num_runs = 5
    run_count = 0
    for run in range(num_runs):
        filename = 'iperf_%s_%s_to_%s_%d.txt' % (test_type,
            client, server, run)
        throughput = get_throughput(filename)
        if throughput is not None:
            host_pair_sum += get_throughput(filename)
            run_count += 1
    return host_pair_sum * 1.0/num_runs;

def get_average_throughput(hosts, test_type, link_capacity=None):
    throughput_sum = 0
    num_flows = 0
    for client, server in pairwise(hosts):
        host_pair_avg = get_average_throughput_per_pair(client, server, test_type)
        if host_pair_avg is not None:
            if link_capacity is not None:
                throughput_sum += host_pair_avg * 1.0 / link_capacity[(client, server)]
                num_flows += 1
                continue
            throughput_sum += host_pair_avg
            num_flows += 1
    return throughput_sum * 1.0 / num_flows

def get_link_capacity(hosts):
    link_capacity = {}

    for client, server in pairwise(hosts):
        host_pair_avg = get_average_throughput_per_pair(client, server, 'baseline')
        link_capacity[(client, server)] = host_pair_avg

    return link_capacity

def make_table1():
    hosts = []
    with open('graph.json', 'r') as fp:
        adj_dict = json.load(fp)
        for i in range(0, len(adj_dict.keys())):
            hosts.append('h'+str(i))

    # (client, server) => capacity in mbits/sec
    link_capacity = get_link_capacity(hosts)

    # get throughput percentage for tcp 1 flow 8-shortest paths
    shortest8_1flow = get_average_throughput(hosts, 'shortest8_1flow', link_capacity)
    print 'shortest8_1flow', shortest8_1flow

    # get throughput percentage for tcp 8 flows 8-shortest paths
    shortest8_8flow = get_average_throughput(hosts, 'shortest8_8flow', link_capacity)
    print 'shortest8_8flow', shortest8_8flow

    # get throughput percentage for tcp 1 flow ecmp
    ecmp_1flow = get_average_throughput(hosts, 'ecmp_1flow', link_capacity)
    print 'ecmp_1flow', ecmp_1flow

    # get throughput percentage for tcp 8 flows ecmp
    ecmp_8flow = get_average_throughput(hosts, 'ecmp_8flow', link_capacity)
    print 'ecmp_8flow', ecmp_8flow

    print "Generating table of results..."
    columns = ('ECMP', '8-shortest paths')
    rows = ['TCP 1 flow', 'TCP 8 flow']
    cell_text = [[ecmp_1flow, shortest8_1flow],
                [ecmp_8flow, shortest8_8flow]]

    fig, axs = plt.subplots(2,1)
    axs[0].axis('tight')
    axs[0].axis('off')
    the_table = axs[0].table(cellText=cell_text,
                             colLabels=columns,
                             rowLabels=rows,
                             loc='center')

    axs[1].plot(cell_text[0],cell_text[1])

    filename = 'table1_withbaseline.png'
    plt.savefig(filename)

    print "Done. Created table in file:", filename


def main():
    make_table1()

if __name__ == "__main__":
    main()