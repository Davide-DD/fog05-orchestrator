import os
from ..utils import get_address, load_descriptor, get_data_files, load_data, get_nodes_mapping
import random
import json
import requests
from ..inspectable_architecture import InspectableArchitecture
import time


class GossipLearningArchitecture(InspectableArchitecture):

    def __init__(self):
        descriptor_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'descriptors')
        
        edge_file = os.path.join(descriptor_dir_path, 'edge.json')
        thing_file = os.path.join(descriptor_dir_path, 'thing.json')

        edge_edge_net_file = os.path.join(descriptor_dir_path, 'edge-edge-network.json')
        edge_thing_net_file = os.path.join(descriptor_dir_path, 'edge-thing-network.json')

        self.entities_d = {'edge': load_descriptor(edge_file), 'thing': load_descriptor(thing_file)}
        
        self.networks_d = {'edge-edge': load_descriptor(edge_edge_net_file), 'edge-thing': load_descriptor(edge_thing_net_file)}
        
        self.entities_i = {}



    def configure(self,configuration):
        self.edge_nodes_number = int(configuration['edge_nodes_number'])
        self.peers_per_node = int(configuration['peers_per_edge'])



    def associate(self,fog05_api,environment,args):
        self.fog05_api = fog05_api
        self.process_port = args['process_port']
        self.environment = environment
        


    def deploy(self,data):
        print('\nGOSSIP LEARNING ARCHITECTURE - STARTING DEPLOYMENT...')

        print('Finding a mapping...')
        nodes = self.get_mapping('deploy')
        if not nodes:
            raise('Mapping not found!')

        print('Creating networks...')
        
        for n in self.networks_d.values():
            self.fog05_api.network.add_network(n)
        

        print('Creating edge nodes...')
        
        edge_nodes = []
        self.entities_i['edge_nodes'] = edge_nodes
        edge_uuid = self.entities_d['edge']['uuid']
        for i in range(0, self.edge_nodes_number):

            command = "#cloud-config\nruncmd:\n  - [ sh, -xc, 'python3 -u /home/ubuntu/code/server.py " + str(self.peers_per_node) + " "

            if i < self.peers_per_node:
                for j in range(0, i):
                    index = random.randrange(0, i)
                    address = get_address(self.fog05_api, self.entities_i['edge_nodes'][index], 'eth1')
                    command += address + ":" +  self.process_port + " "
            else:
                for j in range(0, self.peers_per_node):
                    index = random.randrange(0, i)
                    address = get_address(self.fog05_api, self.entities_i['edge_nodes'][index], 'eth1')
                    command += address + ":" +  self.process_port + " "

            command += "> /home/ubuntu/log.txt' ]"

            self.entities_d['edge']['configuration']['script'] = command

            self.fog05_api.fdu.onboard(self.entities_d['edge'])

            edge_nodes.append(self.fog05_api.fdu.instantiate(edge_uuid, nodes['edge']))

            if i < self.peers_per_node or i == self.edge_nodes_number - 1:
                time.sleep(15)
        
        time.sleep(30)

        print('Loading data to edge nodes...')
        edge_files = get_data_files(data)
        for i in range(0, len(self.entities_i['edge_nodes'])):
            address = get_address(self.fog05_api, self.entities_i['edge_nodes'][i], 'eth0') + ':' + self.process_port
            files = {'profile.txt': open(edge_files['edge'][i]['profile.txt'], 'r'), 'TS1.txt': open(edge_files['edge'][i]['TS1.txt'], 'r'), 
            'TS2.txt': open(edge_files['edge'][i]['TS2.txt'], 'r'), 'TS3.txt': open(edge_files['edge'][i]['TS3.txt'], 'r'), 
            'TS4.txt': open(edge_files['edge'][i]['TS4.txt'], 'r')}
            load_data(address,files)


        print('GOSSIP LEARNING ARCHITECTURE - DEPLOYMENT COMPLETE!\n')


    def serve(self,data):
        print('\nGOSSIP LEARNING ARCHITECTURE - STARTING SERVE...')

        print('Finding a mapping...')
        nodes = self.get_mapping('serve')
        if not nodes:
            raise('Mapping not found!')

        print('Creating thing...')
        
        edge_thing_address = 'http://' + get_address(self.fog05_api, self.entities_i['edge_nodes'][0], 'eth2') + ':' + self.process_port
        command = "#cloud-config\nruncmd:\n  - [ sh, -xc, 'python3 -u /home/ubuntu/code/client.py " + edge_thing_address + " > /home/ubuntu/log.txt' ]"
        self.entities_d['thing']['configuration']['script'] = command
        
        self.fog05_api.fdu.onboard(self.entities_d['thing'])
        
        self.entities_i['thing'] = self.fog05_api.fdu.instantiate(self.entities_d['thing']['uuid'], nodes['thing'])

        print('GOSSIP LEARNING ARCHITECTURE - SERVE COMPLETE!\n')



    def undeploy(self):
        print('\nGOSSIP LEARNING ARCHITECTURE - STARTING UNDEPLOYMENT...')

        print('Terminating edge nodes...')
        
        for edge_node in self.entities_i['edge_nodes']:
            try:
                self.fog05_api.fdu.terminate(edge_node)
            except Exception as e:
                print(e)
        self.entities_i.pop('edge_nodes')
        self.fog05_api.fdu.offload(self.entities_d['edge']['uuid'])
        

        print('Terminating thing...')
        try:
            self.fog05_api.fdu.terminate(self.entities_i['thing'])
        except Exception as e:
            print(e)
        self.entities_i.pop('thing')
        self.fog05_api.fdu.offload(self.entities_d['thing']['uuid'])
        

        print('Terminating networks...')
        
        for n in self.networks_d.values():
            self.fog05_api.network.remove_network(n['uuid'])
        

        print('GOSSIP LEARNING ARCHITECTURE - UNDEPLOYMENT COMPLETE!\n')



    def check_status(self):
        active_edge_nodes = 0
        for edge_node in self.entities_i['edge_nodes']:
            if get_address(self.fog05_api, edge_node, 'eth0'):
                active_edge_nodes += 1
                break
        return active_edge_nodes >= (self.edge_nodes_number / 2)


    def get_mapping(self,operation='deploy'):
        return get_nodes_mapping(self.fog05_api, self.__get_requirements(operation), self.environment)


    def __get_requirements(self,operation='deploy'):
        requirements = {}

        
        # Recupera i requisiti necessari dal descriptor
        for k, v in self.entities_d.items():
            requirements[k] = {}

        # Aggiunge, se esistono, altri requisiti specifici dell'architettura
        requirements['thing']['level'] = 0
        requirements['edge']['level'] = 1
        

        return requirements


    def get_auxiliary_endpoint(self):
        # Recupero l'entità che offre un endpoint da cui è possibile recuperare i dati computati di utilità
        # Restituisco l'endpoint (come indirizzo:porta/nome) da cui è possibile recuperare i dati di cui sopra
        return ''
