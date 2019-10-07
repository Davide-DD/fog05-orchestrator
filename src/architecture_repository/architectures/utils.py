import json
import requests
import os


def read_file(file_path):
    with open(file_path, 'r') as f:
        data = f.read()
        f.close()
    return data

def get_address(fog05_api,entity,interface):
    result = fog05_api.fdu.instance_info(entity)['hypervisor_info']['network'][interface]['addresses'][0]['address']
    print('Indirizzo: ' + result)
    return result

def load_descriptor(descriptor):
    return json.loads(read_file(descriptor))

def get_data_files(data):
    result = {}
    for node in os.listdir(data):
        if 'DS_Store' not in node:
            node_path = os.path.join(data, node)
            result[node] = {}
            for dataset in os.listdir(node_path):
                if 'DS_Store' not in dataset:
                    dataset_path = os.path.join(node_path, dataset)
                    index = int(dataset)
                    result[node].update({index: {}})
                    for file in os.listdir(dataset_path):
                        result[node][index].update({file: os.path.join(dataset_path, file)})
    return result

def load_data(address, files):
    endpoint = 'http://' + address + '/load_data'
    r = requests.post(endpoint, files=files)

def __check_compatibility(node, constraint, value):
	# Sottrarre alla capacità del nodo le risorse necessarie all'allocazione dei nodi già in esecuzione e mappati su di esso e controllare se la differenza basta a mappare l'entità considerata
	return True
	'''
	if requirement == 'os':
		if self.fog05_api.node.info(node)[constraint] == value:
			return True
		else:
			return False
	elif requirement == 'ram':
		if self.fog05_api.node.info(node)[constraint] == value:
			return True
		else:
			return False
	'''
	# Da implementare:
	# cpu, disks, io, accelerator, network, position
	# Guardare il file fos_types.atd

def get_nodes_mapping(fog05_api, arch_requirements, environment):
	nodes = fog05_api.node.list()
	if len(nodes) == 0:
		print('No compatible mapping found!')
		return None

	result = {}
	for entity, node_requirements in arch_requirements.items():
		for node in nodes:
			compatible = True
			for constraint, value in node_requirements.items():
				compatible = __check_compatibility(node, constraint, value)
			if compatible:
				result[entity] = node
				break

	if len(result.keys()) == len(arch_requirements.keys()):
		return result
	else:
		return None
