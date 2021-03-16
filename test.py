
from config import read_config
from terminus_rpc import TerminusRpc

config = read_config()

t = TerminusRpc(config)

r = t.call(['getinfo'])
print(r)
