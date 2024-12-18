import rclpy
from rclpy.node import Node
from pymongo import MongoClient
from datetime import datetime, timedelta
import time

class DynamicObjectClearanceNode(Node):
    def __init__(self, mongo_uri="mongodb://localhost:27017/", expiration_time_seconds=300):
        super().__init__('dynamic_object_clearance_node')

        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client['shared_database']
        self.map_collection = self.db['map']

        # Set expiration time for dynamic objects (default: 5 minutes)
        self.expiration_time_seconds = expiration_time_seconds

        # Start periodic dynamic object cleanup
        self.get_logger().info(f"Dynamic Object Clearance Node Initialized with expiration time of {self.expiration_time_seconds} seconds.")
        self.periodically_remove_expired_dynamic_objects()

    def remove_expired_dynamic_objects(self):
        """Remove dynamic objects that have been in the map longer than the expiration time."""
        current_time = datetime.now()

        # Find dynamic objects in the map
        dynamic_objects = self.map_collection.find({"static": False})  # Only dynamic objects

        for obj in dynamic_objects:
            timestamp = obj.get("timestamp")
            if timestamp:
                # Calculate time difference
                time_diff = current_time - timestamp
                if time_diff > timedelta(seconds=self.expiration_time_seconds):
                    # Object is expired, so remove it from the map
                    self.map_collection.delete_one({"_id": obj["_id"]})
                    self.get_logger().info(f"Removed expired dynamic object at {obj['coordinates']} (Added: {timestamp})")

    def periodically_remove_expired_dynamic_objects(self):
        """Periodically call remove_expired_dynamic_objects every X seconds."""
        while rclpy.ok():
            # Remove expired dynamic objects from the map
            self.remove_expired_dynamic_objects()
            # Sleep for the specified interval before checking again
            time.sleep(self.expiration_time_seconds)

def main(args=None):
    rclpy.init(args=args)

    # Create the dynamic object clearance node and start the cleanup process
    dynamic_object_clearance_node = DynamicObjectClearanceNode()

    # Spin the node so it can keep running
    rclpy.spin(dynamic_object_clearance_node)

    # Shutdown the ROS2 node when the spinning ends
    dynamic_object_clearance_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()