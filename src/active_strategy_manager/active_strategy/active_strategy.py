from .watcher import Watcher


class ActiveStrategy:

	def __init__(self,main_arch,last_active_main_arch,last_active_auxiliary_archs,association_args,data_name,strategy,manage_function):
		self.main_arch = main_arch
		self.last_active_main_arch = last_active_main_arch
		self.last_active_auxiliary_archs = last_active_auxiliary_archs
		self.association_args = association_args
		self.data_name = data_name
		self.strategy = strategy
		self.watcher = Watcher(self, lambda status: manage_function(self, status))


	def stop_watcher(self):
		self.watcher.stop()
		self.watcher.watch.join()
