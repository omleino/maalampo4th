# app.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# -------------- APUTOIMINNOT -------------- #
def laske_kustannukset_50v(investointi, omaisuuden_myynti, laina_aika, korko,
                            sahkon_hinta, sahkon_kulutus,
                            korjaus_vali, korjaus_hinta, korjaus_laina_aika,
                            sahkon_inflaatio):

    vuodet = 50
    lainan_maara = investointi - omaisuuden_myynti
    lyhennys = lainan_maara / laina_aika
    jaljella = lainan_maara
    hinta = sahkon_hinta

    kustannukset = []
    korjauslainat = []

    for v in range(1, vuodet + 1):

        # Investointilaina
        lyh = lyhennys if v <= laina_aika else 0
        korko_inv = jaljella * (korko / 100) if v <= laina_aika else 0
        if v <= laina_aika:
            jaljella -= lyh

        # Sähkölasku
        sahko = hinta * sahkon_kulutus

        # Uusi korjauslaina (esim. huoltokaivo tms.)
        if v > 1 and (v - 1) % korjaus_vali == 0:
            korjauslainat.append({
                "jaljella": korjaus_hinta,
                "lyh": korjaus_hinta / korjaus_laina_aika,
                "vuosia": korjaus_laina_aika
            })

        korjaus_lyh = korjaus_korot = 0
        for l in korjauslainat:
            if l["vuosia"] > 0:
                korko_l = l["jaljella"] * (korko / 100)
                korjaus_korot += korko_l
                korjaus_lyh += l["lyh"]
                l["jaljella"] -= l["lyh"]
                l["vuosia"] -= 1
        korjauslainat = [l for l in korjauslainat if l["vuosia"] > 0]

        vuosi_kust = lyh + korko_inv + sahko + korjaus_lyh + korjaus_korot
        kustannukset.append(vuosi_kust)

        hinta *= (1 + sahkon_inflaatio / 100)

    return kustannukset


def laske_kaukolampo_kustannukset(kustannus, inflaatio):
    tulos = []
    h = kustannus
    for _ in range(50):
        tulos.append(h)
        h *= (1 + inflaatio / 100)
    return tulos


def diskonttaa(kustannukset, diskontto):
    return [k / ((1 + diskontto / 100) ** i) for i, k in enumerate(kustannukset, 1)]


def npv(kustannukset, diskontto):
    return float(np.sum(diskonttaa(kustannukset, diskontto)))


# -------------- SOVELLUS ------------------ #
st.set_page_config(page_title="Maalämpö vs Kaukolämpö", layout="wide")

st.title("Maalämpö vs Kaukolämpö – 50 vuoden vertailu")

with st.sidebar:
    st.header("Perustiedot")
    investointi = st.number_input("Investointi (€)", min_value=0.0, value=650_000.0, step=10_000.0)
    omaisuuden_myynti   = st.number_input("Myyntitulo (€)", 100_000.0, step=10_000.0)
    laina_aika          = st.slider("Investointilaina (v)", 5, 40, 20)
    korko               = st.number_input("Korko (%/v)", 3.0, step=0.1)
    diskontto           = st.number_input("Diskonttokorko NPV (%/v)", 4.0, step=0.1)

    st.header("Maalämpö – energia")
    sahkon_hinta        = st.number_input("Sähkön hinta (€/kWh)", 0.12, step=0.01)
    sahkon_inflaatio    = st.number_input("Sähkön inflaatio (%/v)", 2.0, step=0.1)
    sahkon_kulutus      = st.number_input("Sähkönkulutus (kWh/v)", 180_000.0, step=10_000.0)

    st.header("Kaukolämpö")
    kl_kustannus        = st.number_input("Kaukolämpö/vuosi (€)", 85_000.0, step=5_000.0)
    kl_inflaatio        = st.number_input("Kaukolämmön inflaatio (%/v)", 2.0, step=0.1)

    st.header("Menetetyt tuotot")
    kassavirta_kk       = st.number_input("Menetetyn omaisuuden kassavirta (€/kk)", 0.0, step=100.0)

    st.header("Korjaukset (maalämpö)")
    korjaus_vali        = st.slider("Korjausväli (v)", 5, 30, 15)
    korjaus_hinta       = st.number_input("Korjauksen hinta (€)", 20_000.0, step=5_000.0)
    korjaus_laina_aika  = st.slider("Korjauslaina (v)", 1, 30, 10)

    st.header("Vastikelaskenta")
    neliot              = st.number_input("Maksavat neliöt (m²)", 1_000.0, step=100.0)

# -------- LASKELMAT -------- #
vuodet = list(range(1, 51))

kl = laske_kaukolampo_kustannukset(kl_kustannus, kl_inflaatio)
ml_ilman = laske_kustannukset_50v(
    investointi, 0, laina_aika, korko,
    sahkon_hinta, sahkon_kulutus,
    korjaus_vali, korjaus_hinta, korjaus_laina_aika,
    sahkon_inflaatio
)
ml_myynnilla = laske_kustannukset_50v(
    investointi, omaisuuden_myynti, laina_aika, korko,
    sahkon_hinta, sahkon_kulutus,
    korjaus_vali, korjaus_hinta, korjaus_laina_aika,
    sahkon_inflaatio
)

# Menetetyn kassavirran lisäys
ml_myynnilla = [m + kassavirta_kk * 12 for m in ml_myynnilla]

# -------- KUVA ------------- #
fig, ax = plt.subplots()
ax.plot(vuodet, kl,           "--", label="Kaukolämpö")
ax.plot(vuodet, ml_ilman,     label="Maalämpö (ei myyntiä)")
ax.plot(vuodet, ml_myynnilla, label="Maalämpö (myynti)")
ax.set_xlabel("Vuosi")
ax.set_ylabel("Kustannus (€)")
ax.set_title("Lämmityskustannukset 50 v (nimelliset €)")
ax.grid(True)
ax.legend()
st.pyplot(fig, use_container_width=True)

# -------- NPV -------------- #
c1, c2, c3 = st.columns(3)
c1.metric("NPV Kaukolämpö",         f"{npv(kl, diskontto):,.0f} €")
c2.metric("NPV Maalämpö (ei myyntiä)", f"{npv(ml_ilman, diskontto):,.0f} €")
c3.metric("NPV Maalämpö (myynti)",     f"{npv(ml_myynnilla, diskontto):,.0f} €")

# -------- TAULUKKO --------- #
st.markdown("### Vastikkeet €/m²/v (mobiiliystävällinen)")
rivit = list(range(1, 11)) + list(range(15, 51, 5))
taulu = pd.DataFrame({
    "Vuosi": rivit,
    "Kauko €/m²/v":   [kl[v-1] / neliot for v in rivit],
    "ML ei myyntiä":  [ml_ilman[v-1] / neliot for v in rivit],
    "ML myynti":      [ml_myynnilla[v-1] / neliot for v in rivit],
}).set_index("Vuosi")

st.dataframe(
    taulu.style.format("{:.2f}"),
    use_container_width=True,
    height=min(600, 40 + 24 * len(rivit))  # sopiva korkeus mobiilille
)

# -------- 1. VUOSI ---------- #
def vastike(l):
    return l[0] / neliot, l[0] / neliot / 12

k_v, k_kk   = vastike(kl)
m1_v, m1_kk = vastike(ml_ilman)
m2_v, m2_kk = vastike(ml_myynnilla)

st.markdown("### Ensimmäisen vuoden vastikkeet")
st.write(f"Kaukolämpö: **{k_v:.2f} €/m²/v** | {k_kk:.2f} €/m²/kk")
st.write(f"Maalämpö (ei myyntiä): **{m1_v:.2f} €/m²/v** | {m1_kk:.2f} €/m²/kk")
st.write(f"Maalämpö (myynti): **{m2_v:.2f} €/m²/v** | {m2_kk:.2f} €/m²/kk")
