from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Create or access the database
db = client["shared_database"]

# Initialize Task Collection
task_collection = db["tasks"]

# Define initial tasks
tasks = [
    {
        "TaskID": 1,
        "TextualDescription": "Fire Alert: Go to fire hydrant",
        "GoalCoordinate": {"x": 5, "y": 10},
        "Status": "Pending",
        "AssignedTo": None,
        "Type": "goal",
        "Priority": 1,
        "AssignmentTime": None,
        "CompletionTime": None,
    },
    {
        "TaskID": 2,
        "TextualDescription": "Patrolling",
        "GoalCoordinate": {"x": 9.5, "y": 9.5},
        "Status": "Pending",
        "AssignedTo": None,
        "Type": "routine",
        "Priority": 2,
        "AssignmentTime": None,
        "CompletionTime": None,
    },
    {
        "TaskID": 3,
        "TextualDescription": "Identify items in shelf and cabinet",
        "GoalCoordinate": {"x": 2, "y": 6},
        "Status": "Pending",
        "AssignedTo": None,
        "Type": "goal",
        "Priority": 3,
        "AssignmentTime": None,
        "CompletionTime": None,
    },
    {
        "TaskID": 4,
        "TextualDescription": "Inspect the carton",
        "GoalCoordinate": {"x": 3, "y": 8},
        "Status": "Pending",
        "AssignedTo": None,
        "Type": "goal",
        "Priority": 4,
        "AssignmentTime": None,
        "CompletionTime": None,
    },
    {
        "TaskID": 5,
        "TextualDescription": "Go to conference table",
        "GoalCoordinate": {"x": 7, "y": 5},
        "Status": "Pending",
        "AssignedTo": None,
        "Type": "goal",
        "Priority": 5,
        "AssignmentTime": None,
        "CompletionTime": None,
    },
    {
        "TaskID": 6,
        "TextualDescription": "Go to person 1",
        "GoalCoordinate": {"x": 9, "y": 3},
        "Status": "Pending",
        "AssignedTo": None,
        "Type": "goal",
        "Priority": 6,
        "AssignmentTime": None,
        "CompletionTime": None,
    }
]

# Insert tasks into the collection
task_collection.insert_many(tasks)

print("Tasks inserted into TaskCollection.")