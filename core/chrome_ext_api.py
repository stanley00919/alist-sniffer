import threading
from flask import Flask, request, jsonify
from PyQt6.QtCore import QObject, pyqtSignal


class ChromeExtServer(QObject):
    url_received = pyqtSignal(str)

    def __init__(self, port: int = 9527):
        super().__init__()
        self.port = port
        self._app = Flask(__name__)
        self._app.logger.disabled = True
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        self._register_routes()

    def _register_routes(self):
        server = self

        @self._app.route('/ping', methods=['GET'])
        def ping():
            return jsonify({'status': 'ok'})

        @self._app.route('/sniff', methods=['POST'])
        def sniff():
            data = request.get_json(force=True, silent=True) or {}
            url = data.get('url', '').strip()
            if url:
                server.url_received.emit(url)
                return jsonify({'status': 'ok', 'url': url})
            return jsonify({'status': 'error', 'message': 'No URL provided'}), 400

    def start(self):
        t = threading.Thread(
            target=self._app.run,
            kwargs={'host': '127.0.0.1', 'port': self.port, 'debug': False, 'use_reloader': False},
            daemon=True
        )
        t.start()
