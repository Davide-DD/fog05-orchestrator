from .architecture import Architecture


class InspectableArchitecture(Architecture):


	def get_auxiliary_endpoint(self):
		raise NotImplementedError()