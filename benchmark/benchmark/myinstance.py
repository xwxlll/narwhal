# Copyright(C) Facebook, Inc. and its affiliates.
import boto3
from botocore.exceptions import ClientError
from collections import defaultdict, OrderedDict
from time import sleep

from benchmark.utils import Print, BenchError, progress_bar
from benchmark.settings import Settings, SettingsError


class AWSError(Exception):
    def __init__(self, error):
        assert isinstance(error, ClientError)
        self.message = error.response['Error']['Message']
        self.code = error.response['Error']['Code']
        super().__init__(self.message)

#------------------------------------------------------------------------------------------
class InstanceManager:
    INSTANCE_NAME = 'dag-node'
    SECURITY_GROUP_NAME = 'dag'
    # 在InstanceManager的构造函数中，传入一个settings对象作为参数，并进行类型检查。
    # 然后，创建一个有序字典（self.clients）用于存储AWS EC2客户端对象，键为AWS区域（settings.aws_regions），值为使用boto3库创建的EC2客户端对象。
    def __init__(self, settings):
        assert isinstance(settings, Settings)  #Settings类自动加载load函数，并且传参给settings
        self.settings = settings
        self.clients = OrderedDict() #字典，键值对是（区域，EC2客户端对象）
        for region in settings.aws_regions:
            self.clients[region] = boto3.client('ec2', region_name=region) 
   
    # make是一个类方法，用于创建InstanceManager的实例。--------------------------------------------------------------------
    @classmethod
    def make(cls, settings_file='settings.json'):  #传入了配置文件setting.json
        try:
            return cls(Settings.load(settings_file))  
        except SettingsError as e:
            raise BenchError('Failed to load settings', e)
    # 获得所有实例的id,ip值------------------------------------------------------------------------------------------------------------
    # 使用_get方法获取具有特定状态（'pending', 'running', 'stopping', 'stopped'）的实例ID。这些状态表示实例处于启动中、运行中、停止中或已停止的状态。
    def _get(self, state):
        # Possible states are: 'pending', 'running', 'shutting-down', 'terminated', 'stopping', and 'stopped'.
        ids, ips = defaultdict(list), defaultdict(list)
        for region, client in self.clients.items():
            r = client.describe_instances(
                Filters=[
                    {
                        'Name': 'tag:Name',
                        'Values': [self.INSTANCE_NAME]
                    },
                    {
                        'Name': 'instance-state-name',
                        'Values': state
                    }
                ]
            )
            instances = [y for x in r['Reservations'] for y in x['Instances']]
            for x in instances:
                ids[region] += [x['InstanceId']]
                if 'PublicIpAddress' in x:
                    ips[region] += [x['PublicIpAddress']]
        return ids, ips
    #-------------------加一个==================================================================
    def get_instance_details(regions,state):
        overall_ids = defaultdict(list)
        overall_ips = defaultdict(list)
        
        for region in regions:
            ec2_client = boto3.client('ec2', region_name=region)
            response = ec2_client.describe_instances()
            instances = response['Reservations'][0]['Instances']
            ids = defaultdict(list)
            ips = defaultdict(list)
            
            for instance in instances:
                instance_id = instance['InstanceId']
                private_ip = instance['PrivateIpAddress']
                public_ip = instance.get('PublicIpAddress', 'N/A')

                ids[region].append(instance_id)
                if public_ip != 'N/A':
                    ips[region].append(public_ip)

            # Merge the current region's IDs and IPs into the overall dictionaries
            for key, value in ids.items():
                overall_ids[key].extend(value)
            for key, value in ips.items():
                overall_ips[key].extend(value)

        return overall_ids, overall_ips
        
    def _wait(self, state):
        # Possible states are: 'pending', 'running', 'shutting-down',
        # 'terminated', 'stopping', and 'stopped'.
        while True:
            sleep(1)
            ids, _ = self._get(state)
            if sum(len(x) for x in ids.values()) == 0:
                break

    def _create_security_group(self, client):
        client.create_security_group(
            Description='HotStuff node',
            GroupName=self.SECURITY_GROUP_NAME,
        )

        client.authorize_security_group_ingress(
            GroupName=self.SECURITY_GROUP_NAME,
            IpPermissions=[
                {
                    'IpProtocol': 'tcp',
                    'FromPort': 22,
                    'ToPort': 22,
                    'IpRanges': [{
                        'CidrIp': '0.0.0.0/0',
                        'Description': 'Debug SSH access',
                    }],
                    'Ipv6Ranges': [{
                        'CidrIpv6': '::/0',
                        'Description': 'Debug SSH access',
                    }],
                },
                {
                    'IpProtocol': 'tcp',
                    'FromPort': self.settings.base_port,
                    'ToPort': self.settings.base_port + 2_000,
                    'IpRanges': [{
                        'CidrIp': '0.0.0.0/0',
                        'Description': 'Dag port',
                    }],
                    'Ipv6Ranges': [{
                        'CidrIpv6': '::/0',
                        'Description': 'Dag port',
                    }],
                }
            ]
        )

    def _get_ami(self, client):
        # The AMI changes with regions.
        response = client.describe_images(
            Filters=[{
                'Name': 'description',
                'Values': ['Canonical, Ubuntu, 20.04 LTS, amd64 focal image build on 2020-10-26']
            }]
        )
        return response['Images'][0]['ImageId']
    
    # 通过client得到这个区域的AMI ID********************************************************************
    def _get_ami_id(self, client):
        response = client.describe_images(
            Owners=['self']
        )
        ami_list = response['Images']
        if len(ami_list) >= 1:
            ami_id = ami_list[0]['ImageId']
            return ami_id
        else:
            # 处理没有或多个AMI的情况
            # 如果没有AMI，你可以选择抛出异常或返回一个默认的AMI ID
            # 如果有多个AMI，你可以选择返回其中一个或进行其他适当的处理
            # 根据你的需求进行相应的处理
            print(" 没有获取到AMI！！！")
            return "ami-07a24fdaac8dfe404"
            

    def create_instances(self, instances):   #接受一个整数参数instances，表示要创建的实例数量。使用assert语句来确保instances是一个正整数。
        assert isinstance(instances, int) and instances > 0

        # Create the security group in every region. 在每个区域中创建安全组，确保在每个区域中的实例都具有相同的安全组设置。安全组是一种虚拟防火墙，用于控制进出EC2实例的网络流量。
        for client in self.clients.values():
            try:
                self._create_security_group(client)
            except ClientError as e:
                error = AWSError(e)
                if error.code != 'InvalidGroup.Duplicate':
                    raise BenchError('Failed to create security group', error)

        try:
            # Create all instances. 创建实例 指定实例的AMI ID、实例类型、密钥对、安全组等。创建的实例数量为instances，并在每个区域中创建相同数量的实例。
            size = instances * len(self.clients)
            progress = progress_bar(                                                 #一个可视化的进度条
                self.clients.values(), prefix=f'Creating {size} instances'
            )
            for client in progress:     
                client.run_instances(
                    ImageId=self._get_ami_id(client),    #获取镜像,使用的区域中自己保存过的Ami **************************************************8
                    InstanceType=self.settings.instance_type,
                    KeyName=self.settings.key_name,
                    MaxCount=instances,
                    MinCount=instances,
                    SecurityGroups=[self.SECURITY_GROUP_NAME],
                    TagSpecifications=[{
                        'ResourceType': 'instance',
                        'Tags': [{
                            'Key': 'Name',
                            'Value': self.INSTANCE_NAME
                        }]
                    }],
                    EbsOptimized=True,
                    BlockDeviceMappings=[{
                        'DeviceName': '/dev/sda1',
                        'Ebs': {
                            'VolumeType': 'gp2',
                            'VolumeSize': 200,
                            'DeleteOnTermination': True
                        }
                    }],
                )

            # Wait for the instances to boot.
            Print.info('Waiting for all instances to boot...')
            self._wait(['pending'])
            Print.heading(f'Successfully created {size} new instances')
        except ClientError as e:
            raise BenchError('Failed to create AWS instances', AWSError(e))

    def terminate_instances(self):
        try:
            ids, _ = self._get(['pending', 'running', 'stopping', 'stopped'])
            size = sum(len(x) for x in ids.values())
            if size == 0:
                Print.heading(f'All instances are shut down')
                return

            # Terminate instances.
            for region, client in self.clients.items():
                if ids[region]:
                    client.terminate_instances(InstanceIds=ids[region])

            # Wait for all instances to properly shut down.
            Print.info('Waiting for all instances to shut down...')
            self._wait(['shutting-down'])
            for client in self.clients.values():
                client.delete_security_group(
                    GroupName=self.SECURITY_GROUP_NAME
                )

            Print.heading(f'Testbed of {size} instances destroyed')
        except ClientError as e:
            raise BenchError('Failed to terminate instances', AWSError(e))
#。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。。
    def start_instances(self, max):
        size = 0
        try:
            ids, _ = self._get(['stopping', 'stopped'])
            for region, client in self.clients.items():
                if ids[region]:
                    target = ids[region]
                    target = target if len(target) < max else target[:max]
                    size += len(target)
                    client.start_instances(InstanceIds=target)
            Print.heading(f'Starting {size} instances')
        except ClientError as e:
            raise BenchError('Failed to start instances', AWSError(e))

    def stop_instances(self):
        try:
            ids, _ = self._get(['pending', 'running'])
            for region, client in self.clients.items():
                if ids[region]:
                    client.stop_instances(InstanceIds=ids[region])
            size = sum(len(x) for x in ids.values())
            Print.heading(f'Stopping {size} instances')
        except ClientError as e:
            raise BenchError(AWSError(e))

    def hosts(self, flat=False):
        try:
            _, ips = self._get(['pending', 'running'])
            return [x for y in ips.values() for x in y] if flat else ips
        except ClientError as e:
            raise BenchError('Failed to gather instances IPs', AWSError(e))

    def print_info(self):
        hosts = self.hosts()
        key = self.settings.key_path
        text = ''
        for region, ips in hosts.items():
            text += f'\n Region: {region.upper()}\n'
            for i, ip in enumerate(ips):
                new_line = '\n' if (i+1) % 6 == 0 else ''
                text += f'{new_line} {i}\tssh -i {key} ubuntu@{ip}\n'
        print(
            '\n'
            '----------------------------------------------------------------\n'
            ' INFO:\n'
            '----------------------------------------------------------------\n'
            f' Available machines: {sum(len(x) for x in hosts.values())}\n'
            f'{text}'
            '----------------------------------------------------------------\n'
        )
