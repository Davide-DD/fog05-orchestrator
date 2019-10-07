class ArchitectureDataRepository:


	def __init__(self):
		self.architecture_data = {}


	def add_architecture_data(self, arch_name, data_name, deploy_files_paths, serve_files_paths):
		self.architecture_data[arch_name] = {data_name: {'deploy': deploy_files_paths, 'serve': serve_files_paths}}