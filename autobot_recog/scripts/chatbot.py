import os
import rclpy
from rclpy.node import Node
from openai import OpenAI
import json
from dotenv import load_dotenv
from pymongo import MongoClient
from bot_package.config import locations


# Load OpenAI API key from .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class ChatbotNode(Node):
    def __init__(self, mongo_uri="mongodb://localhost:27017/"):
        super().__init__('chatbot_node')
        self.mongo_client = MongoClient(mongo_uri)
        self.db = self.mongo_client['shared_database']

        # MongoDB collections
        self.map_collection = self.db['map']
        self.robot_collection = self.db['robots']
        self.tasks_collection = self.db['tasks']

        # Timer for query input (simulate user interaction in ROS)
        self.timer = self.create_timer(3.0, self.process_user_query)

        # Available objects in the environment
        self.available_objects = locations

        self.get_logger().info("Chatbot node initialized and running...")

    def process_user_query(self):
        # Simulate user input query
        query = input('Provide the task: ')

        # Prepare prompt for OpenAI
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an assistant that processes user queries to prioritize locations for tasks. "
                    "Provide two lists based on the user query and the available objects."
                ),
            },
            {
                "role": "user",
                "content": f"""
The available objects in the environment are: {', '.join(self.available_objects)}.
A user provides a query, and you must output two lists:

1. The first list (possible_places) contains all possible locations the user might go to, ranked by priority. 
   This list should include both explicitly mentioned places and any other relevant places inferred from the query.
2. The second list (proximity) determines whether the user's query implies proximity:
   - If the query explicitly suggests proximity (e.g., "nearby," "close," "far"), output "close" or "far" based on the context.
   - If the query does not suggest proximity, output "none."

Query: {query} """
            }
        ]

        # Call OpenAI API
        response = client.chat_completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0,
            max_tokens=200
        )
        output = response.choices[0].message.content.strip()

        self.get_logger().info(f"LLM response: {output}")
        self.get_logger().info(f"Task '{query}' assigned to at {(9.5,9.5)}.")


        # Parse response and assign task if valid
        # self.handle_response(query, output)

    def handle_response(self, query, response):
        parsed_response = json.loads(response)
        possible_places = parsed_response.get("possible_places", [])
        proximity = parsed_response.get("proximity", "none")

        if possible_places:
            # Assign the first location as the task
            object_label = possible_places[0]

            # Fetch coordinates from the map collection using object_label
            location_data = self.map_collection.find_one({"object_label": object_label})
            if location_data:
                coordinates = location_data["coordinate"]
            else:
                self.get_logger().warn(f"Coordinates for object_label '{object_label}' not found in the database.")
                return

            # Get the current highest task ID from the database
            current_highest_task = self.tasks_collection.find_one(
                sort=[("TaskID", -1)]
            )
            task_id = (current_highest_task["TaskID"] + 1) if current_highest_task else 1

            # Insert the new task into the TaskCollection
            new_task = {
                "TaskID": task_id,
                "TextualDescription": query,
                "GoalCoordinate": coordinates,
                "Status": "pending",
                "AssignedTo": None,
                "Type": "goal",  # Set type as dynamic since it comes from user input
                "Priority": 1,  # Assign highest priority to dynamic tasks
                "AssignmentTime": None,
                "CompletionTime": None,
            }
            self.tasks_collection.insert_one(new_task)
            self.get_logger().info(f"Task '{query}' assigned to object '{object_label}' at {coordinates}.")
        else:
            self.get_logger().warn("No valid places found in the response.")


def main(args=None):
    rclpy.init(args=args)
    chatbot_node = ChatbotNode()
    try:
        rclpy.spin(chatbot_node)
    except KeyboardInterrupt:
        chatbot_node.get_logger().info("Shutting down chatbot node...")
    finally:
        chatbot_node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
