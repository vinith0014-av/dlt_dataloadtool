import pandas as pd

df = pd.read_excel('config/ingestion_config.xlsx', sheet_name='SourceConfig')
print('='*60)
print('BACKUP CONFIG - Enabled Jobs:')
print('='*60)
enabled = df[df['enabled'].str.upper() == 'Y']
print(f'Total enabled jobs: {len(enabled)}')
print('\nJobs to run:')
for idx, row in enabled.iterrows():
    print(f"{idx+1}. {row['source_type']}.{row['source_name']}.{row['table_name']} - {row['load_type']}")
print('='*60)
