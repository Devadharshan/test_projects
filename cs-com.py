import pandas as pd

# Load the CSV
df = pd.read_csv("env_memory.csv")

# Clean columns to avoid extra unnamed ones
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

# Normalize app name to extract only app name (e.g., app1)
def extract_app_name(name):
    return name.split('/')[-1] if isinstance(name, str) else None

# Apply and extract values
apps = []

for i in range(len(df)):
    prod_name = df.loc[i, 'prod_name']
    qa_name = df.loc[i, 'qa_name']
    uat_name = df.loc[i, 'uat_name']
    
    app = extract_app_name(prod_name)
    
    prod_mem = df.loc[i, 'prod_memory']
    qa_mem = df.loc[i, 'qa_memory']
    uat_mem = df.loc[i, 'uat_memory']
    
    # Convert memory to integers
    try:
        prod_mem = int(prod_mem)
        qa_mem = int(qa_mem)
        uat_mem = int(uat_mem)
    except:
        continue

    apps.append({
        'app': app,
        'prod_memory': prod_mem,
        'qa_memory': qa_mem,
        'uat_memory': uat_mem,
        'qa_diff': prod_mem - qa_mem,
        'uat_diff': prod_mem - uat_mem
    })

# Create result dataframe
result_df = pd.DataFrame(apps)

# Show results
print(result_df)