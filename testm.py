import psutil
import time

# 定义记录文件路径
log_file = 'system_metrics.log'

# 定义记录间隔时间（秒）
log_interval = 200

def record_system_metrics():
    # 打开记录文件
    with open(log_file, 'a') as file:
        # 获取当前时间戳
        timestamp = int(time.time())
        
        # 获取系统所有进程的信息
        processes = psutil.process_iter(['pid', 'name', 'memory_info', 'connections'])
        for process in processes:
            pid = process.info['pid']
            name = process.info['name']
            memory_info = process.info['memory_info']
            connections = process.info['connections']
            
            # 记录内存信息
            rss = memory_info.rss  # 物理内存占用量（字节）
            vms = memory_info.vms  # 虚拟内存占用量（字节）
            
            # 记录连接数，处理连接信息为空的情况
            num_connections = len(connections) if connections is not None else 0
            
            # 构造输出信息
            output = f"Timestamp: {timestamp}, PID: {pid}, Name: {name}, RSS: {rss}, VMS: {vms}, Connections: {num_connections}"
            
            # 写入记录到文件
            file.write(output + "\n")
            print(output)  # 打印输出信息到控制台（可选）
    
    # 休眠指定时间
    time.sleep(log_interval)

# 运行记录函数
record_system_metrics()
