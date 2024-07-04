tables = cursor.tables(tableType='TABLE')
table_list = [table.table_name for table in tables]
print("Tables:")
print(table_list)