from .strategy import Strategy
import copy


class StrategyRepository:


	def __init__(self, architecture_repository):
		self.architecture_repository = architecture_repository
		self.strategies = []


	def define_strategy(self, main_arch_dict, replacement_archs_dicts=[], auxiliary_archs_dicts=[]):
		main_arch = self.__get_and_configure_arch(list(main_arch_dict.keys())[0], list(main_arch_dict.values())[0])
		
		replacement_archs = []
		for r in replacement_archs_dicts:
			replacement_archs.append(self.__get_and_configure_arch(list(r.keys())[0], list(r.values())[0]))

		auxiliary_archs = []
		for a in auxiliary_archs_dicts:
			auxiliary_archs.append(self.__get_and_configure_arch(list(a.keys())[0], list(a.values())[0]))

		if main_arch:
			self.strategies.append(Strategy(main_arch, replacement_archs, auxiliary_archs))
			print('\nStrategy added!\n')
			return len(self.strategies) - 1

		print('\nError in adding the strategy...\n')
		return - 1


	def __get_and_configure_arch(self, arch_name, configuration):
		arch = self.architecture_repository.architectures.get(arch_name)
		copied_arch = copy.deepcopy(arch)
		copied_arch.configure(configuration)
		return copied_arch
