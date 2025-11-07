import os
import multiprocessing

bind = f"0.0.0.0:{os.environ.get('PORT', '5000')}"

workers = int(os.environ.get('WEB_CONCURRENCY', '2'))

worker_class = 'gevent'

threads = 1

worker_connections = 1000

max_requests = 1000
max_requests_jitter = 50

timeout = 60

keepalive = 5

preload_app = True

accesslog = '-'
errorlog = '-'
loglevel = 'info'

def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_fork(server, worker):
    pass

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("worker received INT or QUIT signal")

def worker_abort(worker):
    worker.log.info("worker received SIGABRT signal")
