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
