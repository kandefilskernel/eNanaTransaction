import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# Configuration de la page
st.set_page_config(layout="wide")

# 1. Chargement des données
@st.cache_data
def load_data():
    return pd.read_csv("Transactions_data.csv")

df = load_data()
st.write("Aperçu des données chargées:", df.head())  # Afficher les premières lignes

# 2. Titre du tableau de bord
st.title("Dashboard Interactif - Analyse des Transactions")

# 3. Sidebar - Filtres dynamiques
st.sidebar.header("Filtres")

# Conversion de TransactionStartTime si présente
if 'TransactionStartTime' in df.columns:
    df['TransactionStartTime'] = pd.to_datetime(df['TransactionStartTime'], errors='coerce')
    st.write("Aperçu des dates:", df['TransactionStartTime'].describe())

    # Supprimer les lignes avec des dates invalides
    df = df.dropna(subset=['TransactionStartTime'])

    date_min = df['TransactionStartTime'].min()
    date_max = df['TransactionStartTime'].max()
    date_range = st.sidebar.date_input("Filtrer par Date", [date_min.date(), date_max.date()])

    if len(date_range) == 2:
        st.write("Plage de dates sélectionnée:", date_range)
        
        # Filtrer les données par date
        df = df[(df['TransactionStartTime'] >= pd.to_datetime(date_range[0])) & 
                 (df['TransactionStartTime'] <= pd.to_datetime(date_range[1]))]
        
        st.write("Données après filtrage par date:", df.head())

# 4. Gestion des valeurs négatives dans les montants
cols = ['Amount']
df[cols] = df[cols].replace(0, np.nan).mask(df[cols] < 0, np.nan)  # Remplacer 0 par NaN et masquer les valeurs négatives

# Calcul de la médiane pour remplacer les NaN
median_value = df['Amount'].median()
df['Amount'].fillna(median_value, inplace=True)  # Remplacer les NaN par la médiane

# Afficher les montants après remplacement
st.write("Montants après remplacement des valeurs négatives par la médiane :", df['Amount'].describe())

# 5. Analyse des transactions par jour
transactions_per_day = df.groupby('TransactionStartTime').size()
st.bar_chart(transactions_per_day)  # Visualiser le nombre de transactions par jour

# 6. Revenus par catégorie
revenue_per_category = df.groupby('ProductCategory')['Value'].sum().sort_values(ascending=False).reset_index()
fig = px.bar(revenue_per_category, x='ProductCategory', y='Value',
             title="Revenu total par catégorie de produit", color='Value')
st.plotly_chart(fig)

# 7. Options pour exclure les valeurs négatives
if st.sidebar.checkbox("Exclure les valeurs négatives", value=True):
    df = df[df[cols] >= 0]
    st.write("Données après exclusion des valeurs négatives :", df.head())

# 8. Filtres catégoriels multiples
colonnes_categorique = df.select_dtypes(include=['object', 'category']).columns.tolist()
st.write("Colonnes catégorielles détectées:", colonnes_categorique)

for col in colonnes_categorique:
    valeurs = df[col].unique().tolist()
    selection = st.sidebar.multiselect(f"{col}", valeurs, default=valeurs)
    df = df[df[col].isin(selection)]

# 9. Sélection pour Graphiques
colonnes_numerique = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
st.write("Colonnes numériques détectées:", colonnes_numerique)

col_x = st.sidebar.selectbox("Variable X (catégorique)", colonnes_categorique)
col_y = st.sidebar.selectbox("Variable Y (numérique)", colonnes_numerique)
col_color = st.sidebar.selectbox("Variable couleur (optionnel)", [None] + colonnes_categorique)

# 10. Affichage de Graphiques
if 'TransactionStartTime' in df.columns:
    st.subheader("Évolution temporelle")
    line_data = df.groupby('TransactionStartTime')[col_y].mean().reset_index()
    fig_line = px.line(line_data, x='TransactionStartTime', y=col_y, title=f"{col_y} moyen au fil du temps")
    st.plotly_chart(fig_line, use_container_width=True)

# 11. Analyse tabulaire
st.subheader("Analyse Tabulaire")
groupby_col = st.selectbox("Grouper par", colonnes_categorique)
agg_col = st.multiselect("Colonnes à agréger", colonnes_numerique, default=colonnes_numerique[:1])
if groupby_col and agg_col:
    st.dataframe(df.groupby(groupby_col)[agg_col].agg(['mean', 'sum', 'count']).round(2))

# 12. Données brutes
with st.expander("Aperçu des données"):
    st.dataframe(df)

# 13. Téléchargement des données filtrées
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Télécharger les données filtrées", csv, "transactions_filtrées.csv", "text/csv")
