import threading
import time


class Watcher:

	def __init__(self, active_strategy, function, pause=10):
		self.to_stop = False
		self.bypass = False
		self.watch = threading.Thread(target=self.__watch, args=(active_strategy, function, pause))
		self.watch.start()


	def stop(self):
		self.to_stop = True


	def toggle_bypass(self):
		self.bypass = not self.bypass


	def __watch(self, active_strategy, function, pause):
		while not self.to_stop:
			if not self.bypass:
				actual_status = ''
				if active_strategy.last_active_main_arch == active_strategy.main_arch:
					if active_strategy.last_active_main_arch.check_status():
						actual_status = 'main-active'
					else:
						actual_status = 'needs-replacement'
				else:
					if active_strategy.main_arch.get_mapping():
						actual_status = 'main-ready'
					elif active_strategy.last_active_main_arch.check_status():
						actual_status = 'replacement-active'
					else:
						actual_status = 'needs-replacement'
				if actual_status == 'needs-replacement' or actual_status == 'main-ready':
					function(actual_status)
			time.sleep(pause)
