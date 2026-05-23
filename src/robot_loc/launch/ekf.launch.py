from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os

def generate_launch_description():

    ekf_config = os.path.expanduser(
            '/workspace/src/robot_loc/config/ekf_params.yaml'
    )
    

    namespace = LaunchConfiguration('namespace')

    return LaunchDescription([

        DeclareLaunchArgument(
            'namespace',
             default_value='robot1',
            description='Robot namespace'
               ),

        Node(
            package='robot_localization',
            executable='ekf_node',
            namespace=namespace,
            name='ekf_filter_node',
            output='screen',
            parameters=[ekf_config],
            remappings=[('/tf', '/robot1/tf'), ('/tf_static', '/robot1/tf_static'), ('tf', '/robot1/tf'), ('tf_static', '/robot1/tf_static')]
        )
    ])
