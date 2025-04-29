import pandas as pd

# Load the CSV
df = pd.read_csv("env_memory.csv")

# Remove unnecessary columns (Unnamed)
df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

# Helper to extract app name
def extract_app_name(name):
    return name.split('/')[-1] if isinstance(name, str) else None

# Collect apps with memory differences
apps_with_diff = []

for i in range(len(df)):
    prod_name = df.loc[i, 'prod_name']
    qa_name = df.loc[i, 'qa_name']
    uat_name = df.loc[i, 'uat_name']
    
    app = extract_app_name(prod_name)
    
    prod_mem = df.loc[i, 'prod_memory']
    qa_mem = df.loc[i, 'qa_memory']
    uat_mem = df.loc[i, 'uat_memory']
    
    try:
        prod_mem = int(prod_mem)
        qa_mem = int(qa_mem)
        uat_mem = int(uat_mem)
    except:
        continue

    # Check if there's a memory difference
    if not (prod_mem == qa_mem == uat_mem):
        apps_with_diff.append({
            'app': app,
            'prod_memory': prod_mem,
            'qa_memory': qa_mem,
            'uat_memory': uat_mem
        })

# Create result dataframe
result_df = pd.DataFrame(apps_with_diff)

# Show results
print(result_df)