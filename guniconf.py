
# for deployments!

bind = '0.0.0.0:5000'
workers = 3

# log to stdout - handy for docker
accesslog = '-'

# log to to stderr - handy for docker
# errorlog = '-'
# loglevel = 'info'

# accesslog simplified format, plus timing.
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s %(L)s'
