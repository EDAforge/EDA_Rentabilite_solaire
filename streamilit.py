import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_option_menu import option_menu
import random
import plotly.graph_objects as go
import numpy as np
from streamlit_pdf_viewer import pdf_viewer


data = pd.read_csv("sol_sud.csv")
revente = pd.read_csv("revente.csv")
ray_aq = pd.read_csv("ray_aq.csv")
ray_oc = pd.read_csv("ray_oc.csv")
cons1 = pd.read_csv("consommation_electrique_hiver_ete.csv")

st.set_page_config(page_title="Dashbord", page_icon="⛅", layout="wide")

st.header("💵 La rentabilité de l'Energie Solaire")
st.warning("⚙️ Le prix moyen ne prend pas en compte l'instalation ")
st.sidebar.image("header.jpg", caption = "Fait par EDA_Forge")
st.sidebar.markdown("Filtres")
#region
region = st.sidebar.multiselect("Choisissez la Région:", options= data["administrative_area_level_1"].unique(), default = data["administrative_area_level_1"].unique())
data = data[data['administrative_area_level_1'].apply(lambda x: x in region)]
if region == "Occitanie":
     ray = ray_oc
elif region == "Nouvelle-Aquitaine":
     ray = ray_aq
else:
     ray = random.choice([ray_aq, ray_oc])

#season
season = st.sidebar.radio("Choisissez la Saison:", options = ["Hiver", "Ete"])
ray = ray[ray["Saison"] == season]
if season == "Hiver":
    seson = "consommation_Wh_hiver"
elif season == "Ete":
    seson = "consommation_Wh_ete"


jours = [jour for jour in ray["Année"].unique()]
choix = random.choice(jours)
if st.sidebar.button("Changer de jour"):
     choix = random.choice(jours)



#Fait interressant
pui_m, prix_m, ensol_m , prix_re = st.columns(4)
with pui_m:
    st.info("Puissance crete Minumum")
    st.metric(label= "puissance", label_visibility="hidden", value = f"{int(data["puissance_crete"].min())} W")
with prix_m:
    st.info("Prix: 1 panneau/1 onduleur")
    st.metric(label = "prix", label_visibility="hidden" , value = f"{int(data["Prix_total"].mean())} €")
with ensol_m:
    st.info("Ensoleillement Moyen")
    st.metric(label = "prix", label_visibility="hidden" , value = f"{int(ray[ray["Année"] == choix].loc[ray["Année"] == choix, "Rayonnement solaire global (W/m2)"].mean())} W/m²")
with prix_re:
    st.info("Prix de revente moyen")
    st.metric(label = "Heure creuse" ,label_visibility="hidden", value = f"0.{int(ray[["Tarif ≤ 3 kWc","Tarif ≤ 9 kWc"]].mean().mean())} €/kwh")

with st.expander("Rapport"):

    pdf_viewer("Rentabilité du Solaire.pdf",
    width=700,
    height=1000,
    zoom_level=1.2,
    viewer_align="center",
    show_page_separator=True,
    render_text=True
    )

    st.download_button(
        "📥 Télécharger le PDF",
        data= "Rentabilité du Solaire.pdf",
        file_name="Rentabilité du Solaire.pdf",
        mime="application/pdf"
    )

##RENTABILITE
st.markdown(f"### Rentabilité le {choix}")
fig = go.Figure()
cons1 = cons1.rename(columns={"heure": "Heure"})
cons1["Heure"] = cons1["Heure"].apply(lambda x: x+":00")
df = ray[ray['Année'] == choix].sort_values(by = "Heure", ascending = True)

df_merged = pd.merge(df, cons1, on="Heure", how="outer").sort_values("Heure")
df_merged["Energie (W.h-1.m2-1)"] = df_merged["Energie (W.h-1.m2-1)"]*0.18
df_merged = df_merged.fillna(0)[["Heure","Saison","Energie (W.h-1.m2-1)",seson]]

df_merged = df_merged[df_merged["Heure"].isin(df["Heure"].unique())].drop_duplicates(keep="first").reset_index().drop(columns = "index")
df_merged["Heure"] = df_merged["Heure"].drop_duplicates(keep = "first")

df_merged[seson] = df_merged[seson]/100


df_merged["Recharge_Batterie"] = np.where(df_merged["Energie (W.h-1.m2-1)"] > df_merged[seson],
                                  abs(df_merged["Energie (W.h-1.m2-1)"] - df_merged[seson]),0)

df_merged["Utilisation_Batterie"] = np.where(df_merged[seson] > df_merged["Energie (W.h-1.m2-1)"],
                                              abs(df_merged["Energie (W.h-1.m2-1)"] - df_merged[seson]), 0)


df_merged["Heure"] = df_merged["Heure"].apply(lambda x: x[0:2] + "H")

surface = st.number_input("Entrez une surface (par défaut elle est egale a 1m²)", step=1)



if surface == 0:
     surface = 1

a,b = st.columns(2)
with a:
    st.text("Prix de revent de energie: ")
    if df_merged["Recharge_Batterie"].sum() <= 3:
        st.info(f"{(df_merged["Recharge_Batterie"].sum()*(df["Tarif ≤ 3 kWc"].max()/100)*surface).round(2)} €")
    else:
        st.info(f"{(df_merged["Recharge_Batterie"].sum()*(df["Tarif ≤ 9 kWc"].max()/100)*surface).round(2)} €")
with b:
    st.text("Consommation cher le founisseur ou batteries: ")
    st.info(f"{(df_merged["Utilisation_Batterie"].sum()).round(2)} Wh")



fig.add_trace(go.Scatter(x = df_merged["Heure"], y = df_merged["Energie (W.h-1.m2-1)"],
                          fill ="tozeroy",name="Rayonnement (W.h-1.m-²)"))
#x = df_merged["Heure"],



#fig.add_trace(go.Bar(x = df_merged["Heure"], y = df_merged["consommation_Wh_hiver"]))
fig.add_trace(go.Bar(x= df_merged["Heure"], y = df_merged[seson], name="Consommation (W.h-1.m-²)"))
fig.add_trace(go.Bar(x = df_merged["Heure"], y = df_merged["Recharge_Batterie"], name="Recharge de la Batterie / Revente" )) 
fig.add_trace(go.Scatter(x = df_merged["Heure"], y = df_merged["Utilisation_Batterie"], name= "Utilisation de la Batterie / Reseau publique"))

max_y = max(
    df_merged["Energie (W.h-1.m2-1)"].max(),
    (df_merged[seson] + df_merged["Recharge_Batterie"]).max()
)
fig.update_layout(barmode='stack',
                   title = "Gestion de la consomartion et production d'énergie",
                   xaxis_title="Temps", yaxis_title="Energie (W.h-1.m-²)", colorway = px.colors.qualitative.Vivid)

st.plotly_chart(fig)


with st.expander("### Production"):
    carte, ensol = st.columns(2)
    with carte:
            st.markdown("#### Localisation des panneaux solaire")
            fig = px.scatter_geo(data,
                            lat="lat",
                            lon= "lon",
                            scope = "europe")

            fig.update_geos(
                lonaxis_range=[-5.5, 9.6],
                lataxis_range=[41, 51.5],

                showframe=False,
                showocean=True,  
                showland=True,
                landcolor="#262730",  # <<< couleur du fond FR ici
                countrycolor="gray"
            )

            fig.update_layout(
                margin=dict(l=0, r=0, t=0, b=0)
            )



            st.plotly_chart(fig)


    with ensol:
        st.markdown("#### Rayonnement absorbé par un panneau solaire")
        fig1 = px.area(ray[ray['Année'] == choix].sort_values(by = "Heure", ascending = True),
                        x = "Heure", y = "Energie (W.h-1.m2-1)" ,
                        title= choix, ).update_traces(line_shape="spline")
        st.plotly_chart(fig1.update_layout(yaxis_title = "Energie (W.h-1.m-²)"))

        if  surface != 0:
            ray["Energie (W/h)"] = ray["Energie (W.h-1.m2-1)"] * surface
            st.info(f"Energie Moyenne : {int(ray['Energie (W/h)'].mean()*0.2)} W/h")
        

## CONSOMMATION
with st.expander("### Consomation d'un francais en moyenne"):
    fig2 = px.histogram(cons1, x = "Heure", y = seson,)
    st.plotly_chart(fig2)


#https://www.les-energies-renouvelables.eu/conseils/photovoltaique/tarif-rachat-electricite-photovoltaique/
