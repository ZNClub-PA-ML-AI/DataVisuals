
import pandas as pd
df = pd.read_clipboard()
print(df)

df.to_csv('data/irda_health_insurance_2021.csv')


#%%
import pandas as pd
df = pd.read_clipboard()
df
