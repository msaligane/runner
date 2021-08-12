#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import sys, logging, os, json, threading, requests, time, datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def load_fallback():
    fallback_path = os.path.realpath('../src/runnerversion')
    with open(fallback_path, 'r') as f:
        return f.readline().strip()

RV_URL = "https://raw.githubusercontent.com/actions/runner/main/src/runnerversion"
RV_LOCK = threading.Lock()
RV = load_fallback()
RV_T = datetime.datetime.now().isoformat()

def update_rv():
    global RV
    global RV_T

    logging.info("Started update_rv")

    while True:
        try:
            r = requests.get(RV_URL)
            r.raise_for_status()
            with RV_LOCK:
                new_rv = r.text.strip()
                if new_rv != RV:
                    RV = new_rv
                    RV_T = datetime.datetime.now().isoformat()
                    logging.info(f"New RV: {RV}")
        except Exception as e:
            logging.info(f"Exception occured: {str(e)}")
        time.sleep(10)

    logging.info("Stopped update_rv")
            

class RunnerVersionCacheHandler(BaseHTTPRequestHandler):
    def log_request(self, _):
        pass

    def make_resp(self, status, content):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def notfound(self):
        return self.make_resp(404, '')

    def _set_response(self):
        with RV_LOCK:
            j = {"version": RV, "timestamp": RV_T} 

        if self.path != "/":
            return self.make_resp(404, '')

        return self.make_resp(200, json.dumps(j))

    def do_GET(self):
        self._set_response()

def run():
    addr = ('localhost', 15789)
    httpd = HTTPServer(addr, RunnerVersionCacheHandler)
    update_rv_thr = threading.Thread(target=update_rv, daemon=True)

    try:
        update_rv_thr.start()
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()

if __name__ == '__main__':
    run()
