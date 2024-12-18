from setuptools import find_packages, setup
import glob

package_name = 'autobot_recog'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.py')),  # Corrected glob usage
        ('share/' + package_name + '/urdf', glob.glob('urdf/*.xacro')),  # Add this line for the URDF
    ],
    scripts=[
            'scripts/move.py',      
            'scripts/image_save.py',
            'scripts/agent_node.py',  
            'scripts/multi_move.py',
            'scripts/chatbot.py',
            'scripts/master_slave_node.py',
            'scripts/dynamic_object_clearance_node.py',
            'scripts/object_detection.py',



        ],    
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='host',
    maintainer_email='b22me002@iitj.ac.in',
    description='Package for robot movement and waypoint navigation',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'move = move:main',  
            'image_save = image_save:main', 
            'agent_node = agent_node:main',  
            'multi_move = multi_move:main',
            'chatbot = chatbot:main',
            'master_slave_node = master_slave_node:main',
            'dynamic_object_clearance_node = dynamic_object_clearance_node:main',
            'object_detection = object_detection:main',
            
        ],
    },
)
