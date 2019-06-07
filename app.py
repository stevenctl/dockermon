import os

from flask import Flask, request, jsonify, send_from_directory

from monitor import Monitor, DOCKER_CONTAINER_NAME as MONITOR_CONTAINER_NAME
import docker

REACT_PATH="dockermon-ui/build"
app = Flask(__name__, static_folder=REACT_PATH)

docker_client = docker.from_env()
monitor = Monitor(docker_client)


@app.route('/containers')
def get_containers():
    return jsonify(_get_valid_containers())


@app.route('/monitored', methods=['GET'])
def get_monitored_container():
    return monitor.container_name or ('', 404)


@app.route('/monitored', methods=['PUT'])
def set_monitored_container():
    container_name = request.get_data()
    if container_name not in _get_valid_containers():
        return '{} is not a valid container'.format(container_name), 400

    try:
        monitor.monitor(container_name)
    except:
        return 'failed to start monitor on container {}'.format(container_name), 500

    return 'started monitor on container {}'.format(container_name), 201


@app.route('/traffic')
def get_traffic():
    return jsonify(monitor.get_traffic())


def _get_valid_containers():
    containers = docker_client.containers.list()
    return [c.name for c in containers if c.name != MONITOR_CONTAINER_NAME]


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(REACT_PATH + "/" + path):
        return send_from_directory(REACT_PATH, path)
    else:
        return send_from_directory(REACT_PATH, 'index.html')

if __name__ == '__main__':
    app.run(use_reloader=True, port=5000, threaded=True)

