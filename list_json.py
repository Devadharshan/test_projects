import json

output_list = [
    '{"id": 1, "name": "John", "age": 25}',
    '{"id": 2, "name": "Alice", "age": 30}',
    '{"id": 3, "name": "Bob", "age": 22}'
]

# Extracting specific values from each JSON object
desired_values = []
for json_str in output_list:
    try:
        json_obj = json.loads(json_str)
        # Access specific values from the JSON object
        name = json_obj.get("name")
        age = json_obj.get("age")
        
        # Add the desired values to the result list
        desired_values.append({"name": name, "age": age})
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

# Print the result
print(desired_values)



# fix type error part 1

import json

output_list = [
    '{"id": 1, "name": "John", "age": 25}',
    '{"id": 2, "name": "Alice", "age": 30}',
    '{"id": 3, "name": "Bob", "age": 22}'
]

# Extracting specific values from each JSON object
desired_values = []
for json_str in output_list:
    try:
        json_obj = json.loads(json_str)
        # Access specific values from the JSON object
        name = json_obj.get("name")
        age = json_obj.get("age")

        # Check if 'name' and 'age' are present in the JSON object
        if name is not None and age is not None:
            # Add the desired values to the result list
            desired_values.append({"name": name, "age": age})
        else:
            print(f"Error: 'name' or 'age' not found in JSON object: {json_str}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

# Print the result
print(desired_values)

# fix error 2

import json

output_list = [
    '{"id": 1, "name": "John", "age": 25}',
    '{"id": 2, "name": "Alice", "age": 30}',
    '{"id": 3, "name": "Bob", "age": 22}'
]

# Extracting specific values from each JSON object
desired_values = []
for json_str in output_list:
    try:
        if not isinstance(json_str, str):
            raise TypeError(f"Input is not a string: {json_str}")

        json_obj = json.loads(json_str)
        # Access specific values from the JSON object
        name = json_obj.get("name")
        age = json_obj.get("age")

        # Check if 'name' and 'age' are present in the JSON object
        if name is not None and age is not None:
            # Add the desired values to the result list
            desired_values.append({"name": name, "age": age})
        else:
            print(f"Error: 'name' or 'age' not found in JSON object: {json_str}")

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
    except TypeError as te:
        print(te)

# Print the result
print(desired_values)


# convert list to json string

import json

# Example Python list
my_list = [{"id": 1, "name": "John", "age": 25},
           {"id": 2, "name": "Alice", "age": 30},
           {"id": 3, "name": "Bob", "age": 22}]

# Convert the list to a JSON string
json_string = json.dumps(my_list)

# Print the resulting JSON string
print(json_string)



# new change

import json

class State:
    def __init__(self, value):
        self.value = value

def serialize_state(obj):
    if isinstance(obj, State):
        return obj.__dict__
    raise TypeError("Object not serializable")

# Example Python list with custom objects
my_list = [State(1), State(2), State(3)]

# Convert the list to a JSON string using the serialization function
json_string = json.dumps(my_list, default=serialize_state)

# Print the resulting JSON string
print(json_string)
