import pandas as pd

df = pd.read_csv('dataset/OLD_safe-hp-dataset.csv')
print(len(df))
df = df.drop_duplicates()
print(len(df))
df.to_csv('dataset/safe-hp-dataset.csv')

df = pd.read_csv('dataset/OLD_necessary-hp-dataset.csv')
print(len(df))
df = df.drop_duplicates()
print(len(df))
df.to_csv('dataset/necessary-hp-dataset.csv')

df = pd.read_csv('dataset/OLD_belongs-hp-dataset.csv')
print(len(df))
df = df.drop_duplicates()
print(len(df))
df.to_csv('dataset/belongs-hp-dataset.csv')