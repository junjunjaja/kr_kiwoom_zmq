from server_module import Agent
from configparser import ConfigParser
base_config = ConfigParser()
base_config.read('../Private.cfg')
token = base_config['TELEGRAM']['token']
channel = base_config['TELEGRAM']['channel']
base_config.read('../Base_setting.cfg')
IP = base_config['SOCKET']['Producer_Addr']
PORT =base_config['SOCKET']['Port']
PORT2 = base_config['SOCKET']['telePort']
if __name__ == '__main__':
    ag = Agent(binding_ip=IP,port=PORT,token=token,channel_id=channel,teleport=PORT2)
    ag.run_client()
