class Strategy:

	def __init__(self,main_arch,replacement_archs=[],auxiliary_archs=[]):
		self.main_arch = main_arch
		self.replacement_archs = replacement_archs
		self.auxiliary_archs = auxiliary_archs