import sys
from architecture_repository.architectures.federated_learning.federated_learning_architecture import FederatedLearningArchitecture
from architecture_repository.architectures.gossip_learning.gossip_learning_architecture import GossipLearningArchitecture
from architecture_repository.architecture_repository import ArchitectureRepository
from architecture_data_repository.architecture_data_repository import ArchitectureDataRepository
from trail_repository.trail_repository import TrailRepository
from orchestrator.orchestrator import Orchestrator
import time


yaks_address = ''
if len(sys.argv) < 2:
	print('[Usage] {} <yaks_address ip:port>'.format(sys.argv[0]))
	exit(0)
	yaks_address = sys.argv[1]

fla = FederatedLearningArchitecture()
gla = GossipLearningArchitecture()

architecture_repository = ArchitectureRepository()
architecture_repository.add_architecture(fla)
architecture_repository.add_architecture(gla)

architecture_data_repository = ArchitectureDataRepository()
architecture_data_repository.add_architecture_data(fla.__class__.__name__, 'hydraulic-system', 
	'/home/osboxes/Scrivania/one_node_deployment/architecture_data_repository/data/FederatedLearningArchitecture/hydraulic-system/deploy',
	'/home/osboxes/Scrivania/one_node_deployment/architecture_data_repository/data/FederatedLearningArchitecture/hydraulic-system/serve')
architecture_data_repository.add_architecture_data(gla.__class__.__name__, 'hydraulic-system', 
		'/home/osboxes/Scrivania/one_node_deployment/architecture_data_repository/data/GossipLearningArchitecture/hydraulic-system/deploy',
		'/home/osboxes/Scrivania/one_node_deployment/architecture_data_repository/data/GossipLearningArchitecture/hydraulic-system/serve')

trail_repository = TrailRepository(architecture_repository)
fla_config = {'edge_nodes_number': 1, 'edge_nodes_per_aggregator': 1}
gla_config = {'edge_nodes_number': 2, 'peers_per_edge': 1}
trail_index = trail_repository.define_trail({fla.__class__.__name__: fla_config}, [{gla.__class__.__name__: gla_config}])

orchestrator = Orchestrator(architecture_data_repository, trail_repository)
mapper_configuration = {'position': '47.541234, 13.531236'}
association_args = {fla.__class__.__name__: {'process_port': '5000'}, gla.__class__.__name__: {'process_port': '5000'}}
active_trail_index = orchestrator.start_trail(yaks_address, association_args, mapper_configuration, 'hydraulic-system', trail_index)
orchestrator.serve_trail(active_trail_index)
time.sleep(240)
orchestrator.stop_trail(active_trail_index)
