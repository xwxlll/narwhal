# Copyright(C) Facebook, Inc. and its affiliates.
from fabric import task

from benchmark.local import LocalBench
from benchmark.logs import ParseError, LogParser
from benchmark.utils import Print
from benchmark.plot import Ploter, PlotError
# from benchmark.instance import InstanceManager
from benchmark.myinstance import InstanceManager
from benchmark.remote import Bench, BenchError

import re
# + RESULTS:
#  Consensus TPS: 4,265 tx/s
#  Consensus BPS: 2,183,780 B/s
#  Consensus latency: 962 ms

#  End-to-end TPS: 4,181 tx/s
#  End-to-end BPS: 2,140,680 B/s
#  End-to-end latency: 1,253 ms

def extract_Consensus_tps(data):
    tps_values = re.findall(r'Consensus TPS: ([\d,]+)', data)
    # print(values)
    v = [int(value.replace(',', '')) for value in tps_values]
    print(v)
    if len(v) == 0:
        print("数据为0\n")
        min_v = 0
        max_v = 0
        avg_v = 0
    else:
        min_v = min(v)
        max_v = max(v)
        avg_v = sum(v) / len(v)
    return min_v, max_v, avg_v
def extract_Consensus_bps(data):
    bps_values = re.findall(r'Consensus BPS: ([\d,]+)', data)
    # print(bps_values)
    v2 = [int(value.replace(',', '')) for value in bps_values]
    if len(v2)==0:
        min_v=0
        max_v=0
        avg_v=0
    else:
        min_v = min(v2)
        max_v = max(v2)
        avg_v = sum(v2) / len(v2)
    return min_v,max_v,avg_v

def extract_Consensus_latency(data):                                     
    latency = re.findall(r'Consensus latency: ([\d,]+)', data)
    v3 = [int(value.replace(',', '')) for value in latency]
    if len(v3)==0:
        min_v=0
        max_v=0
        avg_v=0
    else:
        min_v = min(v3)
        max_v = max(v3)
        avg_v = sum(v3) / len(v3)
    return min_v,max_v,avg_v

def extract_End_tps(data):
    tps = re.findall(r'End-to-end TPS: ([\d,]+)', data)
    v4 = [int(value.replace(',', '')) for value in tps]
    if len(v4)==0:
        min_v=0
        max_v=0
        avg_v=0
    else:
        min_v = min(v4)
        max_v = max(v4)
        avg_v = sum(v4) / len(v4)
    return min_v,max_v,avg_v


def extract_End_bps(data):
    bps = re.findall(r'End-to-end BPS: ([\d,]+)', data)
    # print(bps)
    v5 = [int(value.replace(',', '')) for value in bps]
    if len(v5)==0:
        min_v=0
        max_v=0
        avg_v=0
    else:
        min_v = min(v5)
        max_v = max(v5)
        avg_v = sum(v5) / len(v5)
    return min_v,max_v,avg_v


def extract_End_latency(data):
    latency = re.findall(r'End-to-end latency: ([\d,]+)', data)
    # print(latency)
    v6 = [int(value.replace(',', '')) for value in latency]
    if len(v6)==0:
        min_v=0
        max_v=0
        avg_v=0
    else:
        min_v = min(v6)
        max_v = max(v6)
        avg_v = sum(v6) / len(v6)
    return min_v,max_v,avg_v
    

def extract_result(datas, param_info):
    min_v = 0
    max_v = 0
    avg_v = 0
    try:
        with open("data/result.txt", 'a') as outfile:
            outfile.write(f"测试参数信息: {param_info}\n")  # extract_End_tps
            try:
                min_v, max_v, avg_v = extract_Consensus_tps(datas)
                info1 = " Consensus TPS :"
                outfile.write(f"{info1}: Min {min_v:<10} Max {max_v:<10} Ave {avg_v:<10} \n")
            except Exception as e:
                print("提取 Consensus TPS 时出错:", e)

            try:
                min_v, max_v, avg_v = extract_Consensus_bps(datas)
                info2 = " Consensus BPS :"
                outfile.write(f"{info2}: Min {min_v:<10} Max {max_v:<10} Ave {avg_v:<10} \n")
            except Exception as e:
                print("提取 Consensus BPS 时出错:", e)

            try:
                min_v, max_v, avg_v = extract_Consensus_latency(datas)
                info3 = " Consensus Latency :"
                outfile.write(f"{info3}: Min {min_v:<10} Max {max_v:<10} Ave {avg_v:<10} \n")
            except Exception as e:
                print("提取 Consensus Latency 时出错:", e)

            try:
                min_v, max_v, avg_v = extract_End_tps(datas)
                info4 = " End-to-end TPS :"
                outfile.write(f"{info4}: Min {min_v:<10} Max {max_v:<10} Ave {avg_v:<10} \n")
            except Exception as e:
                print("提取 End-to-end TPS 时出错:", e)

            try:
                min_v, max_v, avg_v = extract_End_bps(datas)
                info5 = " End-to-end BPS :"
                outfile.write(f"{info5}: Min {min_v:<10} Max {max_v:<10} Ave {avg_v:<10} \n")
            except Exception as e:
                print("提取 End-to-end BPS 时出错:", e)

            try:
                min_v, max_v, avg_v = extract_End_latency(datas)
                info6 = " End-to-end latency:"
                outfile.write(f"{info6}: Min {min_v:<10} Max {max_v:<10} Ave {avg_v:<10} \n")
            except Exception as e:
                print("提取 End-to-end latency 时出错:", e)
    except Exception as e:
        print("写入文件时出错:", e)
# 本地运行
@task
def local(ctx, debug=True):
    for nodes_number in [4]:  #[4,10,20,50]
        for input_rate in[50_000]: #[5_000,50_000,500_000]
            for batch_size in [5_000]: #[5_000,50_000,500_000]
                
                ''' Run benchmarks on localhost '''
                bench_params = {
                    'faults': 0,
                    'nodes': nodes_number,
                    'workers': 1,
                    'rate': input_rate,
                    'tx_size': 512, # B 
                    'duration': 60,
                }
                node_params = {
                    'header_size': 1_000,  # bytes
                    'max_header_delay': 200,  # ms
                    'gc_depth': 100,  # rounds
                    'sync_retry_delay': 10_000,  # ms
                    'sync_retry_nodes': 3,  # number of nodes
                    'batch_size': batch_size,  # bytes
                    'max_batch_delay': 200  # ms
                }

                # 输出每次运行的参数
                param_info="参数 nodes_number = {},input_rate = {},batch_size = {}".format(nodes_number,input_rate,batch_size)
                print(param_info)
                s = "newbench-{}-{}-{}".format(bench_params['nodes'], bench_params['rate'], node_params['batch_size'])
                # 指定保存每次运行输出结果的文件名
                file_name = s+".txt"
                file_path = "data/" + file_name
                # 将输出结果写入文件
                for run_times in range(1): # 每组参数下运行的次数、、、、、、、、、、、、、、、、
                    print("第",run_times,"次")
                    with open(file_path, 'a') as file:      
                        try:
                            ret = LocalBench(bench_params, node_params).run(debug)
                            print(ret.result())
                            # 执行一些操作，生成输出结果
                            output_result = ret.result()
                            # 写入---------------------------------
                            file.write(output_result) 
                            print(f"输出结果已保存到 {file_path} 文件中。")
                        except BenchError as e:
                            Print.error(e)
                # 读出所有结果到datas
                datas = ''
                with open(file_path, 'r') as infile:
                    datas = infile.read()
                    # 运行完10次测试后提取最大值，最小值，平均值写入result.txt
                # print(datas)
                extract_result(datas,param_info)

# 在测试台创建AWS服务器实例
@task
def create(ctx, nodes=1):
    ''' Create a testbed'''
    try:
        InstanceManager.make().create_instances(nodes) #make(cls, settings_file='settings.json')是从默认的参数文件setting.json中传入的实例配置
    except BenchError as e:
        Print.error(e)

# 终止所有AWS实例
@task
def destroy(ctx):
    ''' Destroy the testbed '''
    try:
        InstanceManager.make().terminate_instances()
    except BenchError as e:
        Print.error(e)

# 开启
@task
def start(ctx, max=2):
    ''' Start at most `max` machines per data center '''
    try:
        InstanceManager.make().start_instances(max)
    except BenchError as e:
        Print.error(e)

# 停止
@task
def stop(ctx):
    ''' Stop all machines '''
    try:
        InstanceManager.make().stop_instances()
    except BenchError as e:
        Print.error(e)


@task
def info(ctx):
    ''' Display connect information about all the available machines '''
    try:
        InstanceManager.make().print_info()
    except BenchError as e:
        Print.error(e)

# 下载代码到机器上
@task
def install(ctx):
    ''' Install the codebase on all machines '''
    try:
        Bench(ctx).install()
    except BenchError as e:
        Print.error(e)

# 远程运行
@task
def remote(ctx, debug=False):
    ''' Run benchmarks on AWS '''
    bench_params = {
        'faults': 0,
        'nodes': [5], # 这个应该和create的机器数量一致才对
        'workers': 1,
        'collocate': False,  #是否将同一个node的primary和worker放在同一台机器上，默认True
        'rate': [10_000, 100_000],
        'tx_size': 512,
        'duration': 300,
        'runs': 1,
    }
    node_params = {
        'header_size': 1_000,  # bytes
        'max_header_delay': 200,  # ms
        'gc_depth': 50,  # rounds
        'sync_retry_delay': 10_000,  # ms
        'sync_retry_nodes': 3,  # number of nodes
        'batch_size': 500_000,  # bytes
        'max_batch_delay': 200  # ms
    }
    try:
        Bench(ctx).run(bench_params, node_params, debug)
    except BenchError as e:
        Print.error(e)


@task
def plot(ctx):
    ''' Plot performance using the logs generated by "fab remote" '''
    plot_params = {
        'faults': [0],
        'nodes': [10, 20, 50],
        'workers': [1],
        'collocate': True,
        'tx_size': 512,
        'max_latency': [3_500, 4_500]
    }
    try:
        Ploter.plot(plot_params)
    except PlotError as e:
        Print.error(BenchError('Failed to plot performance', e))

# 停止代码运行
@task
def kill(ctx):
    ''' Stop execution on all machines '''
    try:
        Bench(ctx).kill()
    except BenchError as e:
        Print.error(e)


@task
def logs(ctx):
    ''' Print a summary of the logs '''
    try:
        print(LogParser.process('./logs', faults='?').result())
    except ParseError as e:
        Print.error(BenchError('Failed to parse logs', e))
