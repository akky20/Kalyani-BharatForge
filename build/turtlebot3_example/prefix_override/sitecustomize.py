import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/host/dev_ws/autobot/src/install/turtlebot3_example'
