from ..inspectable_architecture import InspectableArchitecture
import os
from ..utils import get_address, load_descriptor, get_data_files, load_data, get_nodes_mapping
import json
import requests
import time
from .federated_learning_server import create_server, destroy_server


class FederatedLearningArchitecture(InspectableArchitecture):

    def __init__(self):
        descriptor_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'descriptors')
        
        coordinator_file = os.path.join(descriptor_dir_path, 'coordinator.json')
        master_aggregator_file = os.path.join(descriptor_dir_path, 'master_aggregator.json')
        aggregator_file = os.path.join(descriptor_dir_path, 'aggregator.json')
        edge_file = os.path.join(descriptor_dir_path, 'edge.json')
        thing_file = os.path.join(descriptor_dir_path, 'thing.json')

        coordinator_master_aggregator_net_file = os.path.join(descriptor_dir_path, 'coordinator-master_aggregator-network.json')
        coordinator_edge_net_file = os.path.join(descriptor_dir_path, 'coordinator-edge-network.json')
        master_aggregator_aggregator_net_file = os.path.join(descriptor_dir_path, 'master_aggregator-aggregator-network.json')
        aggregator_edge_net_file = os.path.join(descriptor_dir_path, 'aggregator-edge-network.json')
        edge_thing_net_file = os.path.join(descriptor_dir_path, 'edge-thing-network.json')

        self.entities_d = {'coordinator': load_descriptor(coordinator_file), 'master_aggregator': load_descriptor(master_aggregator_file), 
        'aggregator': load_descriptor(aggregator_file), 'edge': load_descriptor(edge_file), 'thing': load_descriptor(thing_file)}
        
        self.networks_d = {'coordinator-master_aggregator': load_descriptor(coordinator_master_aggregator_net_file), 
        'coordinator-edge': load_descriptor(coordinator_edge_net_file), 
        'master_aggregator-aggregator': load_descriptor(master_aggregator_aggregator_net_file), 
        'aggregator-edge': load_descriptor(aggregator_edge_net_file), 'edge-thing': load_descriptor(edge_thing_net_file)}
        
        self.entities_i = {}



    def configure(self,configuration):
        self.edge_nodes_number = int(configuration['edge_nodes_number'])
        self.edge_nodes_per_aggregator = int(configuration['edge_nodes_per_aggregator'])



    def associate(self,fog05_api,environment,args):
        self.fog05_api = fog05_api
        self.environment = environment
        self.process_port = args['process_port']
        


    def deploy(self,data):
        print('\nFEDERATED LEARNING ARCHITECTURE - STARTING DEPLOYMENT...')

        print('Finding a mapping...')
        nodes = self.get_mapping('deploy')
        if not nodes:
            raise('Mapping not found!')

        print('Creating networks...')
        for n in self.networks_d.values():
            self.fog05_api.network.add_network(n)

        print('Creating edge nodes...')
        command = "#cloud-config\nruncmd:\n  - [ sh, -xc, 'python3 -u /home/ubuntu/code/server.py > /home/ubuntu/log.txt' ]"
        self.entities_d['edge']['configuration']['script'] = command
        self.fog05_api.fdu.onboard(self.entities_d['edge'])

        edge_nodes = []
        self.entities_i['edge_nodes'] = edge_nodes
        edge_uuid = self.entities_d['edge']['uuid']
        for i in range(0, self.edge_nodes_number):
            edge_nodes.append(self.fog05_api.fdu.instantiate(edge_uuid, nodes['edge']))

        print('Loading data to edge nodes...')
        time.sleep(30)
        edge_files = get_data_files(data)
        for i in range(0, len(self.entities_i['edge_nodes'])):
            address = get_address(self.fog05_api, self.entities_i['edge_nodes'][i], 'eth0') + ':' + self.process_port
            files = {'profile.txt': open(edge_files['edge'][i]['profile.txt'], 'r'), 'TS1.txt': open(edge_files['edge'][i]['TS1.txt'], 'r'), 
            'TS2.txt': open(edge_files['edge'][i]['TS2.txt'], 'r'), 'TS3.txt': open(edge_files['edge'][i]['TS3.txt'], 'r'), 
            'TS4.txt': open(edge_files['edge'][i]['TS4.txt'], 'r')}
            load_data(address,files)

        print('Creating coordinator...')
        time.sleep(15)
        edge_addresses = []
        for edge_node in self.entities_i['edge_nodes']:
            edge_addresses.append(get_address(self.fog05_api, edge_node, 'eth1') + ':' + self.process_port)

        command = "#cloud-config\nruncmd:\n  - [ sh, -xc, 'python3 -u /home/ubuntu/code/server.py "
        for address in edge_addresses:
            command += address + " "
        command += "> /home/ubuntu/log.txt' ]"
        self.entities_d['coordinator']['configuration']['script'] = command

        self.fog05_api.fdu.onboard(self.entities_d['coordinator'])

        self.entities_i['coordinator'] = self.fog05_api.fdu.instantiate(self.entities_d['coordinator']['uuid'], nodes['coordinator'])

        time.sleep(15)

        print('Creating server...')
        create_server(self.start_task_execution, self.finish_task_execution)

        print('FEDERATED LEARNING ARCHITECTURE - DEPLOYMENT COMPLETE!\n')



    def start_task_execution(self,task):
        print('\nTask execution requested. Task: ' + task['operation'] + '. Auxiliary fog nodes are being deployed...')

        print('Finding a mapping...')
        nodes = self.get_mapping('task')
        if not nodes:
            raise('Mapping not found!')

        aggregators_number = round(self.edge_nodes_number / self.edge_nodes_per_aggregator)

        print('Creating master aggregator...')
        
        coordinator_master_address = get_address(self.fog05_api, self.entities_i['coordinator'], 'eth1') + ':' + self.process_port
        command = "#cloud-config\nruncmd:\n  - [ sh, -xc, 'python3 -u /home/ubuntu/code/server.py " + str(aggregators_number) + " " + coordinator_master_address + " > /home/ubuntu/log.txt' ]"
        self.entities_d['master_aggregator']['configuration']['script'] = command

        self.fog05_api.fdu.onboard(self.entities_d['master_aggregator'])

        self.entities_i['master_aggregator'] = self.fog05_api.fdu.instantiate(self.entities_d['master_aggregator']['uuid'], nodes['master_aggregator'])

        print('Creating aggregators...')
        
        time.sleep(30)
        aggregator_master_address = get_address(self.fog05_api, self.entities_i['master_aggregator'],'eth1') + ':' + self.process_port
        command = "#cloud-config\nruncmd:\n  - [ sh, -xc, 'python3 -u /home/ubuntu/code/server.py " + str(self.edge_nodes_per_aggregator) + " " + aggregator_master_address + " > /home/ubuntu/log.txt' ]"
        self.entities_d['aggregator']['configuration']['script'] = command
        self.fog05_api.fdu.onboard(self.entities_d['aggregator'])

        aggregators = []
        self.entities_i['aggregators'] = aggregators
        for i in range(0, aggregators_number):
            aggregators.append(self.fog05_api.fdu.instantiate(self.entities_d['aggregator']['uuid'], nodes['aggregator']))
        

        print('Communicating to coordinator the task to be executed...')
        
        time.sleep(45)
        aggregators_addresses = []
        for aggregator in self.entities_i['aggregators']:
            aggregators_addresses.append(get_address(self.fog05_api, aggregator, 'eth1') + ':' + self.process_port)
        task['aggregators'] = aggregators_addresses
        print(task['aggregators'])
        coordinator_mgmt_address = get_address(self.fog05_api, self.entities_i['coordinator'], 'eth0') + ':' + self.process_port
        endpoint = 'http://' + coordinator_mgmt_address + '/start'
        r = requests.post(endpoint, json=task)

        print('\nTask is being carried out!')



    def finish_task_execution(self):
        print('\nThe task has been carried out. Starting termination of auxiliary fog nodes...')

        print('Terminating aggregators...')
        
        for aggregator in self.entities_i['aggregators']:
            self.fog05_api.fdu.terminate(aggregator)
        self.entities_i.pop('aggregators')
        self.fog05_api.fdu.offload(self.entities_d['aggregator']['uuid'])
        

        print('Terminating master aggregator...')
        
        self.fog05_api.fdu.terminate(self.entities_i['master_aggregator'])
        self.entities_i.pop('master_aggregator')
        self.fog05_api.fdu.offload(self.entities_d['master_aggregator']['uuid'])
        

        print('Auxiliary fog nodes terminated!\n')



    def serve(self,data):
        print('\nFEDERATED LEARNING ARCHITECTURE - STARTING SERVE...')

        print('Finding a mapping...')
        nodes = self.get_mapping('serve')
        if not nodes:
            raise('Mapping not found!')

        print('Creating thing...')
        
        edge_thing_address = 'http://' + get_address(self.fog05_api, self.entities_i['edge_nodes'][0], 'eth3') + ':' + self.process_port
        command = "#cloud-config\nruncmd:\n  - [ sh, -xc, 'python3 -u /home/ubuntu/code/client.py " + edge_thing_address + " > /home/ubuntu/log.txt' ]"
        self.entities_d['thing']['configuration']['script'] = command
        
        self.fog05_api.fdu.onboard(self.entities_d['thing'])
        
        self.entities_i['thing'] = self.fog05_api.fdu.instantiate(self.entities_d['thing']['uuid'], nodes['thing'])

        print('FEDERATED LEARNING ARCHITECTURE - SERVE COMPLETE!\n')



    def undeploy(self):
        print('\nFEDERATED LEARNING ARCHITECTURE - STARTING UNDEPLOYMENT...')

        print('Terminating server...')
        destroy_server()
 
        if 'aggregators' in self.entities_i:
            self.finish_task_execution()
        

        print('Terminating edge nodes...')
        
        for edge_node in self.entities_i['edge_nodes']:
            try:
                self.fog05_api.fdu.terminate(edge_node)
            except Exception as e:
                print(e)
        self.entities_i.pop('edge_nodes')
        self.fog05_api.fdu.offload(self.entities_d['edge']['uuid'])
        

        print('Terminating coordinator...')
        try:
            self.fog05_api.fdu.terminate(self.entities_i['coordinator'])
            self.entities_i.pop('coordinator')
            self.fog05_api.fdu.offload(self.entities_d['coordinator']['uuid'])
        except Exception as e:
                print(e)

        print('Terminating thing...')
        try:
            self.fog05_api.fdu.terminate(self.entities_i['thing'])
            self.entities_i.pop('thing')
            self.fog05_api.fdu.offload(self.entities_d['thing']['uuid'])
        except Exception as e:
            print(e)

        print('Terminating networks...')
        
        for n in self.networks_d.values():
            self.fog05_api.network.remove_network(n['uuid'])
        

        print('FEDERATED LEARNING ARCHITECTURE - UNDEPLOYMENT COMPLETE!\n')


    def check_status(self): 
        coordinator_status = get_address(self.fog05_api, self.entities_i['coordinator'], 'eth0') != ''
        edge_nodes_status = False
        for edge_node in self.entities_i['edge_nodes']:
            if get_address(self.fog05_api, edge_node, 'eth0'):
                edge_nodes_status = True
                break
        return coordinator_status and edge_nodes_status


    def get_mapping(self,operation='deploy'):
        return get_nodes_mapping(self.fog05_api, self.__get_requirements(operation), self.environment)


    def __get_requirements(self,operation):
        requirements = {}

        # Recupera i requisiti necessari dal descriptor
        for k, v in self.entities_d.items():
            requirements[k] = {}

        # Aggiunge, se esistono, altri requisiti specifici dell'architettura
        requirements['thing']['level'] = 0
        requirements['edge']['level'] = 1
        requirements['aggregator']['level'] = 2
        requirements['master_aggregator']['level'] = 3
        requirements['coordinator']['level'] = 4
        
        return requirements


    def get_auxiliary_endpoint(self):
        # Recupero l'entità che offre un endpoint da cui è possibile recuperare i dati computati di utilità
        # Restituisco l'endpoint (come indirizzo:porta/nome) da cui è possibile recuperare i dati di cui sopra
        return ''
