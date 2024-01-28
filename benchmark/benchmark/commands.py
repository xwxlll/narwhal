# Copyright(C) Facebook, Inc. and its affiliates.
from os.path import join

from benchmark.utils import PathMaker

import os



class CommandMaker:

    @staticmethod
    def cleanup():
        return (
            f'rm -r .db-* ; rm .*.json ; mkdir -p {PathMaker.results_path()}'
        )
    
    # @staticmethod
    # def clean_logs():
    #     # 获取日志目录路径
    #     logs_path = PathMaker.logs_path()

    #     # 构建目标目录的路径
    #     target_dir = 'data'
    #     target_path = os.path.join(os.getcwd(), target_dir)

    #     # 构建新的日志目录路径
    #     new_logs_path = f'{logs_path}_backup'

    #     # 构建移动日志目录的命令
    #     move_command = f'mv {logs_path} {target_path}'

    #     # 构建重命名日志目录的命令
    #     rename_command = f'mv {target_path}/{os.path.basename(logs_path)} {new_logs_path}'

    #     mk_command = f'mkdir -p {PathMaker.logs_path()}'
    #     # 返回移动和重命名日志目录的命令
    #     return f'{move_command} && {rename_command}&& {mk_command}'
    
    @staticmethod
    def clean_logs():
        # 获取日志目录路径
        logs_path = PathMaker.logs_path()

        # 构建目标目录的路径
        target_path = 'data'
        num=1111111
        new_logs_path = 'data/log'+str(num)
        # 返回移动日志目录的命令
        return f'mkdir {new_logs_path}; mv {logs_path} {new_logs_path};rm -r {PathMaker.logs_path()}; mkdir -p {PathMaker.logs_path()}'
    # @staticmethod
    # def clean_logs():
    #     return f'rm -r {PathMaker.logs_path()} ; mkdir -p {PathMaker.logs_path()}'

    @staticmethod
    def compile():
        return 'cargo build --quiet --release --features benchmark'

    @staticmethod
    def generate_key(filename):
        assert isinstance(filename, str)
        return f'./node generate_keys --filename {filename}'

    @staticmethod
    def run_primary(keys, committee, store, parameters, debug=False):
        assert isinstance(keys, str)
        assert isinstance(committee, str)
        assert isinstance(parameters, str)
        assert isinstance(debug, bool)
        v = '-vvv' if debug else '-vv'
        return (f'./node {v} run --keys {keys} --committee {committee} '
                f'--store {store} --parameters {parameters} primary')

    @staticmethod
    def run_worker(keys, committee, store, parameters, id, debug=False):
        assert isinstance(keys, str)
        assert isinstance(committee, str)
        assert isinstance(parameters, str)
        assert isinstance(debug, bool)
        v = '-vvv' if debug else '-vv'
        return (f'./node {v} run --keys {keys} --committee {committee} '
                f'--store {store} --parameters {parameters} worker --id {id}')

    @staticmethod
    def run_client(address, size, rate, nodes):
        assert isinstance(address, str)
        assert isinstance(size, int) and size > 0
        assert isinstance(rate, int) and rate >= 0
        assert isinstance(nodes, list)
        assert all(isinstance(x, str) for x in nodes)
        nodes = f'--nodes {" ".join(nodes)}' if nodes else ''
        return f'./benchmark_client {address} --size {size} --rate {rate} {nodes}'

    @staticmethod
    def kill():
        return 'tmux kill-server'

    @staticmethod
    def alias_binaries(origin):
        assert isinstance(origin, str)
        node, client = join(origin, 'node'), join(origin, 'benchmark_client')
        return f'rm node ; rm benchmark_client ; ln -s {node} . ; ln -s {client} .'
