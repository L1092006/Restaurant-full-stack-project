import multiprocessing
import os
from dotenv import load_dotenv

load_dotenv()

STAGE = os.getenv("STAGE", "DEV")

bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gthread"
threads = 4
timeout = 60
graceful_timeout = 30
if STAGE == "PROD":
    keepalive = 75          # bump to 75 behind an ALB (its idle timeout is 60)
else:
    keepalive = 5          # bump to 75 behind an ALB (its idle timeout is 60)
max_requests = 1000    # recycle workers to blunt slow memory leaks
max_requests_jitter = 50
accesslog = "-"        # stdout, so journald captures it
errorlog = "-"
loglevel = "info"

if STAGE == "PROD":
    # In production, we are behind an ALB, so we need to trust the X-Forwarded-* headers
    forwarded_allow_ips = "*"   # trust X-Forwarded-* — only safe if nothing but the ALB can reach this port