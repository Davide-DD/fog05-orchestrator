from flask import Flask, request
from multiprocessing import Process


server = None
start_function = None
finish_function = None
app = Flask(__name__)

@app.route("/start", methods=['POST'])
def start():
	start_function(request.get_json())
	return 'ok'

@app.route("/finish", methods=['GET'])
def finish():
	finish_function()
	return 'ok'


def create_server(start_callback, finish_callback):
	global start_function, finish_function, server
	start_function = start_callback
	finish_function = finish_callback
	server = Process(target=app.run, kwargs={'host': '0.0.0.0'})
	server.start()


def destroy_server():
	server.terminate()
	server.join()

