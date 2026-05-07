import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from nav2_common.launch import RewrittenYaml


def generate_launch_description():

    bringup_dir = get_package_share_directory('robot_sim_gz')

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    params_file = LaunchConfiguration('params_file')
    autostart = LaunchConfiguration('autostart')
    
    tf_topic = LaunchConfiguration('tf_topic')
    tf_static_topic = LaunchConfiguration('tf_static_topic')


    declare_namespace = DeclareLaunchArgument(
        'namespace',
        default_value='robot1',
        description='Robot namespace'
    )

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use simulation time'
    )

    declare_params_file = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(bringup_dir, 'config', 'nav2_params.yaml'),
        description='Nav2 params file'
    )

    declare_autostart = DeclareLaunchArgument(
        'autostart',
        default_value='true',
        description='Autostart Nav2'
    )
    declare_tf_topic = DeclareLaunchArgument(
        'tf_topic',
        default_value='/tf',
        description='TF topic for Nav2 nodes'
    )
    declare_tf_static_topic = DeclareLaunchArgument(
        'tf_static_topic',
        default_value='/tf_static',
        description='TF static topic for Nav2 nodes'
    )

    # Rewrite params under the namespace
    configured_params = RewrittenYaml(
        source_file=params_file,
        root_key=namespace,
        param_rewrites={'use_sim_time': use_sim_time},
        convert_types=True
    )
    remappings = [('/tf', '/tf'),
                  ('/tf_static', '/tf_static')]

    nav2_nodes = GroupAction([
        PushRosNamespace(namespace),

        Node(
            package='nav2_controller',
            executable='controller_server',
            parameters=[configured_params],
            output='screen',
            remappings=remappings
        ),

        Node(
            package='nav2_planner',
            executable='planner_server',
            parameters=[configured_params],
            output='screen',
            remappings=remappings
        ),

        Node(
            package='nav2_bt_navigator',
            executable='bt_navigator',
            parameters=[configured_params],
            output='screen',
            remappings=remappings
        ),

        Node(
            package='nav2_behaviors',
            executable='behavior_server',
            parameters=[configured_params],
            output='screen',
            remappings=remappings
        ),

        Node(
            package='nav2_waypoint_follower',
            executable='waypoint_follower',
            parameters=[configured_params],
            output='screen',
            remappings=remappings
        ),

        Node(
            package='nav2_velocity_smoother',
            executable='velocity_smoother',
            parameters=[configured_params],
            output='screen',
            remappings=remappings
        ),

        Node(
            package='nav2_lifecycle_manager',
            executable='lifecycle_manager',
            name='lifecycle_manager_navigation',
            parameters=[{
                'use_sim_time': use_sim_time,
                'autostart': autostart,
                'node_names': [
                    'controller_server',
                    'planner_server',
                    'bt_navigator',
                    'behavior_server',
                    'waypoint_follower',
                    'velocity_smoother'
                ]
            }],
            output='screen',
            remappings=remappings
        )
    ])

    return LaunchDescription([
        declare_namespace,
        declare_use_sim_time,
        declare_params_file,
        declare_autostart,
        declare_tf_topic,
        declare_tf_static_topic,
        nav2_nodes
    ])
