import os
from openai import OpenAI
import json
from dotenv import load_dotenv
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Input data
available_objects = ["bookshelf", "cabinet", "cardboard box", "fire hydrant", "table", 
                     "conference table", "lamp", "table", "dustbin", "sofa", "chair"]
query = input('Provide the task: ')

# Prepare prompt
messages = [
    {
        "role": "system",
        "content": (
            "You are an assistant that processes user queries to prioritize locations for tasks."
            " Provide two lists based on the user query and the available objects."
        ),
    },
    {
        "role": "user",
        "content": f"""
The available objects in the environment are: {', '.join(available_objects)}.
A user provides a query, and you must output two lists:

1. The first list (possible_places) contains all possible locations the user might go to, ranked by priority. This list should include both explicitly mentioned places and any other relevant places inferred from the query.
2. The second list (proximity) determines whether the user's query implies proximity:
   - If the query explicitly suggests proximity (e.g., "nearby," "close," "far"), output "close" or "far" based on the context.
   - If the query does not suggest proximity, output "none."

### Key Examples for Guidance:
1. For the query "bring me a book":
   - The output should be:
     {{
       "possible_places": ["bookshelf", "cabinet"],
       "proximity": "none"
     }}
   - No proximity cue, so it defaults to "none."

2. For the query "extinguish the fire asap":
   - The output should be:
     {{
       "possible_places": ["fire_hydrant"],
       "proximity": "close"
     }}
   - The word "asap" implies urgency, hence proximity is categorized as "close."

3. For the query "find me a place to sit nearby":
   - The output should be:
     {{
       "possible_places": ["sofa", "chair"],
       "proximity": "close"
     }}
   - The word "nearby" directly implies proximity as "close."

4. For the query "store the items somewhere far":
   - The output should be:
     {{
       "possible_places": ["cardboard box", "cabinet"],
       "proximity": "far"
     }}
   - The word "far" clearly indicates distance, so proximity is categorized as "far."
5. For the query " join the meeting"
    {{
  "possible_places": ["conference table"],
  "proximity": "none"
    }}
### Instructions:
- Provide the output strictly in the following JSON format:

    "possible_places": "place1", "place2", ...,
    "proximity": "close" | "far" | "none"


Query: {query} """ }, ]

response = client.chat.completions.create( model="gpt-4o-mini", # Use the model available to you 
                                          messages=messages, temperature=0, # Deterministic output 
                                          max_tokens=200 )
output = response.choices[0].message.content.strip() 
print(output)