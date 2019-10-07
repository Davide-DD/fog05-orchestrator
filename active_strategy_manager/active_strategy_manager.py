from fog05 import FIMAPI
import copy
import os
from .active_strategy.active_strategy import ActiveStrategy


def get_and_associate_arch(arch, fog05_api, environment, args):
	copied_arch = copy.deepcopy(arch)
	copied_arch.associate(fog05_api, environment, args)
	return copied_arch


class ActiveStrategyManager:

	def __init__(self,architecture_data_repository, strategy_repository):
		self.architecture_data_repository = architecture_data_repository
		self.strategy_repository = strategy_repository
		self.active_strategies = []


	def start_strategy(self, yaks_address, association_args, environment, data_name, strategy_index):
		print('\nStrategy ' + str(strategy_index) + ': STARTING ACTIVATION...')

		if self.strategy_repository.strategies[strategy_index]:
			fog05_api = FIMAPI(yaks_address)

			strategy = self.strategy_repository.strategies[strategy_index]
			main_arch = get_and_associate_arch(strategy.main_arch, fog05_api, environment, association_args[strategy.main_arch.__class__.__name__])
			if self.__manage_arch(main_arch, True, data_name):
				print('Main architecture started!')

				active_auxiliary_archs = []
				for a in self.strategy_repository.strategies[strategy_index].auxiliary_archs:
					arch = get_and_associate_arch(a, fog05_api, environment, association_args[a.__class__.__name__])
					if self.__manage_arch(arch, True, data_name):
						arch.set_auxiliary_endpoint(main_arch.get_auxiliary_endpoint())
						active_auxiliary_archs.append(arch)

				if len(active_auxiliary_archs) == len(self.strategy_repository.strategies[strategy_index].auxiliary_archs):
					print('All auxiliary architectures started!')
				else:
					print(str(counter) + 'auxiliary architectures started!')

				self.active_strategies.append(ActiveStrategy(main_arch, main_arch, active_auxiliary_archs, association_args,
					data_name, self.strategy_repository.strategies[strategy_index], self.manage_strategy))

				print('Strategy ' + str(strategy_index) + ': ACTIVATION COMPLETE!\n')

				return len(self.active_strategies) - 1

			else:
				print('Error in starting the active strategy, retry!')
				return -1

		else:
			print('You need to add a strategy associated to the architecture you want to deploy before calling this function!')
			return -1


	def serve_strategy(self,active_strategy_index):
		print('\nACTIVE STRATEGY ' + str(active_strategy_index) + ': STARTING SERVE...')
		active_strategy = self.active_strategies[active_strategy_index]
		active_strategy.last_active_main_arch.serve(self.architecture_data_repository.architecture_data[active_strategy.main_arch.__class__.__name__][active_strategy.data_name]['serve'])
		for arch in active_strategy.last_active_auxiliary_archs:
			arch.serve(self.architecture_data_repository.architecture_data[arch.__class__.__name__][active_strategy.data_name]['serve'])
		print('ACTIVE STRATEGY ' + str(active_strategy_index) + ': SERVE COMPLETED!\n')
		return True


	def stop_strategy(self, active_strategy_index):
		print('\nACTIVE STRATEGY ' + str(active_strategy_index) + ': STARTING STOP...')

		active_strategy = self.active_strategies[active_strategy_index]

		active_strategy.stop_watcher()

		if self.__manage_arch(active_strategy.last_active_main_arch, False, active_strategy.data_name):
			print('Main arch stopped!')

			counter = len(active_strategy.last_active_auxiliary_archs)
			for a in active_strategy.last_active_auxiliary_archs:
				if self.__manage_arch(a, False, active_strategy.data_name):
					counter -= 1
			if counter == active_strategy.last_active_auxiliary_archs:
				print('All auxiliary architectures stopped!')
			else:
				print(str(counter) + ' auxiliary architectures stopped!')

			self.active_strategies.pop(active_strategy_index)

			print('ACTIVE STRATEGY ' + str(active_strategy_index) + ': STOP COMPLETED!\n')
			return True

		print('Error in stopping the active strategy, retry!')
		return False


	def manage_strategy(self, active_strategy, status):
		print('\nACTIVE STRATEGY ' + str(active_strategy) + ': STARTING MODIFICATION...')
		
		active_strategy.watcher.toggle_bypass()

		if status == 'main-ready':
			if self.__manage_arch(active_strategy.last_active_main_arch, False, active_strategy.data_name):
				if self.__manage_arch(active_strategy.main_arch, True, active_strategy.data_name):
					active_strategy.main_arch.serve(self.architecture_data_repository.architecture_data[active_strategy.main_arch.__class__.__name__][active_strategy.data_name]['serve'])
					active_strategy.last_active_main_arch = active_strategy.main_arch
					for a in active_strategy.last_active_auxiliary_archs:
						a.set_auxiliary_endpoint(active_strategy.main_arch.get_auxiliary_endpoint())
					print('\nACTIVE STRATEGY ' + str(active_strategy) + ': MODIFICATION COMPLETE!')
				else: 
					print('Error in modifying the active strategy...')
					active_strategy.watcher.toggle_bypass()
					return False
			else:
				print('Error in modifying the active strategy...')
				return False
		elif status == 'needs-replacement':
			if self.__manage_arch(active_strategy.last_active_main_arch, False, active_strategy.data_name):
				replacement, _ = self.__start_replacement(active_strategy.main_arch.fog05_api, active_strategy.association_args,
					active_strategy.main_arch.environment, active_strategy.data_name, active_strategy.strategy, active_strategy.last_active_main_arch, 0)
				if replacement != None:
					replacement.serve(self.architecture_data_repository.architecture_data[replacement.__class__.__name__][active_strategy.data_name]['serve'])
					active_strategy.last_active_main_arch = replacement
					for a in active_strategy.last_active_auxiliary_archs:
						a.set_auxiliary_endpoint(replacement.get_auxiliary_endpoint())
					print('ACTIVE STRATEGY ' + str(active_strategy) + ': MODIFICATION COMPLETE!\n')
				else:
					print('Error in modifying the active strategy...')
					active_strategy.watcher.toggle_bypass()
					return False

		active_strategy.watcher.toggle_bypass()
		return True


	def __start_replacement(self, fog05_api, association_args, environment, data_name, strategy, arch, depth):
		best_replacement_depth = 100
		best_replacement = None
		for r in strategy.replacement_archs:
			arch = get_and_associate_arch(r, fog05_api, environment, association_args[r.__class__.__name__])
			if self.__manage_arch(arch, True, data_name):
				return arch, depth
			else:
				temp_replacement, temp_replacement_depth = self.__start_replacement(fog05_api, association_args, environment, data_name, strategy, r, depth + 1)
				if temp_replacement_depth < best_replacement_depth:
					best_replacement = temp_replacement
					best_replacement_depth = temp_replacement_depth
		return best_replacement, best_replacement_depth


	def __manage_arch(self, arch, deploy, data_name=None):
		try:
			if deploy:
				data = None
				if data_name:
					data = self.architecture_data_repository.architecture_data[arch.__class__.__name__][data_name]['deploy']
				arch.deploy(data)
			else:
				arch.undeploy()
			return True
		except Exception as e:
			print(e)
			if deploy:
				self.__manage_arch(arch, False, data_name)
			return False
