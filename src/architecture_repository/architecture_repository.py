class ArchitectureRepository:

	def __init__(self):
		self.architectures = {}


	def add_architecture(self,architecture):
		self.architectures[architecture.__class__.__name__] = architecture