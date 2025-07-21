import streamlit as st
import pandas as pd
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
    df['TransactionStartTime'] = pd.to_datetime(df['TransactionStartTime'], errors='coerce')  # Convertir en datetime, remplacer les erreurs par NaT
    st.write("Aperçu des dates:", df['TransactionStartTime'].describe())  # Vérifier les dates

    # Supprimer les lignes avec des dates invalides
    df = df.dropna(subset=['TransactionStartTime'])

    date_min = df['TransactionStartTime'].min()
    date_max = df['TransactionStartTime'].max()
    date_range = st.sidebar.date_input("Filtrer par Date", [date_min.date(), date_max.date()])  # Utiliser .date() pour obtenir des objets date

    if len(date_range) == 2:
        st.write("Plage de dates sélectionnée:", date_range)  # Afficher la plage de dates sélectionnée
        
        # Filtrer les données par date
        df = df[(df['TransactionStartTime'] >= pd.to_datetime(date_range[0])) & 
                 (df['TransactionStartTime'] <= pd.to_datetime(date_range[1]))]
        
        st.write("Données après filtrage par date:", df.head())  # Vérifier les données après filtrage

# 4. Option pour exclure les valeurs négatives
if st.sidebar.checkbox("Exclure les valeurs négatives", value=False):
    df = df[df['Amount'] >= 0]
    st.write("Données après exclusion des valeurs négatives :", df.head())

# 5. Filtres catégoriels multiples
colonnes_categorique = df.select_dtypes(include=['object', 'category']).columns.tolist()
st.write("Colonnes catégorielles détectées:", colonnes_categorique)  # Vérifier les colonnes catégorielles

for col in colonnes_categorique:
    valeurs = df[col].unique().tolist()
    selection = st.sidebar.multiselect(f"{col}", valeurs, default=valeurs)
    df = df[df[col].isin(selection)]

# 6. Sélection pour Graphiques
colonnes_numerique = df.select_dtypes(include=['float64', 'int64']).columns.tolist()
st.write("Colonnes numériques détectées:", colonnes_numerique)  # Vérifier les colonnes numériques

col_x = st.sidebar.selectbox("Variable X (catégorique)", colonnes_categorique)
col_y = st.sidebar.selectbox("Variable Y (numérique)", colonnes_numerique)
col_color = st.sidebar.selectbox("Variable couleur (optionnel)", [None] + colonnes_categorique)

# 7. Affichage de Graphiques

# a. Évolution temporelle
if 'TransactionStartTime' in df.columns:
    st.subheader("Évolution temporelle")
    line_data = df.groupby('TransactionStartTime')[col_y].mean().reset_index()
    fig_line = px.line(line_data, x='TransactionStartTime', y=col_y, title=f"{col_y} moyen au fil du temps")
    st.plotly_chart(fig_line, use_container_width=True)

# b. Histogramme
st.subheader("Histogramme interactif")
fig_hist = px.histogram(df, x=col_y, color=col_color, nbins=30)
st.plotly_chart(fig_hist, use_container_width=True)

# c. Barplot (moyenne par catégorie)
st.subheader("Moyenne par catégorie")
agg_data = df.groupby(col_x)[col_y].mean().reset_index()
fig_bar = px.bar(agg_data, x=col_x, y=col_y, color=col_x, title=f"Moyenne de {col_y} par {col_x}")
st.plotly_chart(fig_bar, use_container_width=True)

# d. Heatmap de corrélation
st.subheader("Heatmap de Corrélation")
corr = df[colonnes_numerique].corr()
fig_corr, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
st.pyplot(fig_corr)

# e. Pie chart
if col_x:
    st.subheader("Répartition des catégories")
    fig_pie = px.pie(df, names=col_x, title=f"Répartition de {col_x}")
    st.plotly_chart(fig_pie, use_container_width=True)

# 8. Analyse tabulaire
st.subheader("Analyse Tabulaire")
groupby_col = st.selectbox("Grouper par", colonnes_categorique)
agg_col = st.multiselect("Colonnes à agréger", colonnes_numerique, default=colonnes_numerique[:1])
if groupby_col and agg_col:
    st.dataframe(df.groupby(groupby_col)[agg_col].agg(['mean', 'sum', 'count']).round(2))

# 9. Données brutes
with st.expander("Aperçu des données"):
    st.dataframe(df)

# 10. Téléchargement des données filtrées
csv = df.to_csv(index=False).encode('utf-8')
st.download_button("Télécharger les données filtrées", csv, "transactions_filtrées.csv", "text/csv")
