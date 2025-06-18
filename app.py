import streamlit as st
import matplotlib.pyplot as plt

# ---------------------------
#   APUFUNKTIOITA
# ---------------------------
def laske_kustannukset_50v(investointi, omaisuuden_myynti, investointi_laina_aika, korko,
                            sahkon_hinta, sahkon_kulutus_kwh,
                            korjaus_vali, korjaus_hinta, korjaus_laina_aika,
                            sahkon_inflaatio):

    vuodet = 50
    lainan_maara = investointi - omaisuuden_myynti
    lyhennys = lainan_maara / investointi_laina_aika
    jaljella_oleva_laina = lainan_maara
    sahkon_hinta_vuosi = sahkon_hinta

    kustannukset = []
    korjauslainat = []

    for vuosi in range(1, vuodet + 1):
        # Investointilaina
        if vuosi <= investointi_laina_aika:
            lyh = lyhennys
            korko_investointi = jaljella_oleva_laina * (korko / 100)
            jaljella_oleva_laina -= lyh
        else:
            lyh = 0
            korko_investointi = 0

        sahkolasku = sahkon_hinta_vuosi * sahkon_kulutus_kwh

        # Uusi korjauslaina
        if vuosi > 1 and (vuosi - 1) % korjaus_vali == 0:
            korjauslainat.append({
                "jaljella": korjaus_hinta,
                "lyhennys": korjaus_hinta / korjaus_laina_aika,
                "vuosia_jaljella": korjaus_laina_aika
            })

        # Korjauslainojen lyhennykset ja korot
        korjaus_korko_yht = 0
        korjaus_lyhennys_yht = 0
        for laina in korjauslainat:
            if laina["vuosia_jaljella"] > 0:
                korko_tama = laina["jaljella"] * (korko / 100)
                korjaus_korko_yht += korko_tama
                korjaus_lyhennys_yht += laina["lyhennys"]
                laina["jaljella"] -= laina["lyhennys"]
                laina["vuosia_jaljella"] -= 1

        korjauslainat = [l for l in korjauslainat if l["vuosia_jaljella"] > 0]

        # Vuoden kokonaiskustannus
        kokonais = lyh + korko_investointi + sahkolasku + korjaus_lyhennys_yht + korjaus_korko_yht
        kustannukset.append(kokonais)

        # Päivitä sähkön hinta
        sahkon_hinta_vuosi *= (1 + sahkon_inflaatio / 100)

    return kustannukset


def laske_kaukolampo_kustannukset(kustannus, inflaatio):
    hinta = kustannus
    tulos = []
    for _ in range(50):
        tulos.append(hinta)
        hinta *= (1 + inflaatio / 100)
    return tulos


def diskonttaa_kustannukset(kustannukset, diskontto):
    """Palauttaa listan nykyarvoon diskontatuista kustannuksista (PV)."""
    return [k / ((1 + diskontto / 100) ** vuosi) for vuosi, k in enumerate(kustannukset, 1)]


def npv(kustannukset, diskontto):
    """Yksinkertainen NPV = ∑ PV."""
    return sum(diskonttaa_kustannukset(kustannukset, diskontto))


# ---------------------------
#   STREAMLIT-SOVELLUS
# ---------------------------
def main():
    st.title("Maalämpö vs Kaukolämpö – 50 v vertailu (kaikki vaihtoehdot + NPV)")

    # ----- Syötteet -----
    with st.sidebar:
        st.header("Perustiedot")
        investointi = st.number_input("Investoinnin suuruus (€)", value=650_000.0, step=10_000.0)
        omaisuuden_myynti = st.number_input("Omaisuuden myyntitulo (€)", value=100_000.0, step=10_000.0)
        investointi_laina_aika = st.slider("Investointilainan maksuaika (v)", 5, 40, value=20)
        korko = st.number_input("Lainan korko (% / v)", value=3.0, step=0.1)
        diskontto = st.number_input("Diskonttokorko NPV-laskelmaan (% / v)", value=4.0, step=0.1)

        st.header("Maalämpö – energia")
        sahkon_hinta = st.number_input("Sähkön hinta (€/kWh)", value=0.12, step=0.01)
        sahkon_inflaatio = st.number_input("Sähkön hinnan nousu (% / v)", value=2.0, step=0.1)
        sahkon_kulutus = st.number_input("Maalämmön sähkönkulutus (kWh/v)", value=180_000.0, step=10_000.0)

        st.header("Kaukolämpö")
        kaukolampo_kustannus = st.number_input("Kaukolämmön vuosikustannus (€)", value=85_000.0, step=5_000.0)
        kaukolampo_inflaatio = st.number_input("Kaukolämmön hinnan nousu (% / v)", value=2.0, step=0.1)

        st.header("Menetetyt tuotot")
        menetetty_kassavirta_kk = st.number_input("Menetetyn omaisuuden kassavirta (€ / kk)", value=0.0, step=100.0)

        st.header("Korjaukset (maalämpö)")
        korjaus_vali = st.slider("Korjausväli (v)", 5, 30, value=15)
        korjaus_hinta = st.number_input("Yksittäisen korjauksen hinta (€)", value=20_000.0, step=5_000.0)
        korjaus_laina_aika = st.slider("Korjauslainan maksuaika (v)", 1, 30, value=10)

        st.header("Vastikkeen laskenta")
        maksavat_neliot = st.number_input("Maksavat neliöt (m²)", value=1_000.0, step=100.0)

    # ----- Laskelmat -----
    vuodet = list(range(1, 51))

    kaukolampo = laske_kaukolampo_kustannukset(kaukolampo_kustannus, kaukolampo_inflaatio)

    maalampo_ilman = laske_kustannukset_50v(
        investointi, 0, investointi_laina_aika, korko,
        sahkon_hinta, sahkon_kulutus,
        korjaus_vali, korjaus_hinta, korjaus_laina_aika, sahkon_inflaatio
    )

    maalampo_myynnilla = laske_kustannukset_50v(
        investointi, omaisuuden_myynti, investointi_laina_aika, korko,
        sahkon_hinta, sahkon_kulutus,
        korjaus_vali, korjaus_hinta, korjaus_laina_aika, sahkon_inflaatio
    )

    # Lisätään menetetty vuokrakassavirta
    kassavirta_vuosi = menetetty_kassavirta_kk * 12
    maalampo_myynnilla = [m + kassavirta_vuosi for m in maalampo_myynnilla]

    # ----- NPV-laskelmat -----
    npv_kaukolampo = npv(kaukolampo, diskontto)
    npv_maalampo_ilman = npv(maalampo_ilman, diskontto)
    npv_maalampo_myynnilla = npv(maalampo_myynnilla, diskontto)

    # ----- Kustannuskuvaaja -----
    fig, ax = plt.subplots()
    ax.plot(vuodet, kaukolampo, label="Kaukolämpö", linestyle="--")
    ax.plot(vuodet, maalampo_ilman, label="Maalämpö (ilman myyntiä)")
    ax.plot(vuodet, maalampo_myynnilla, label="Maalämpö (myynti + menetetty kassavirta)")
    ax.set_title("Lämmityskustannukset 50 vuoden ajalla (nimelliset €)")
    ax.set_xlabel("Vuosi")
    ax.set_ylabel("Kustannus (€)")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

    # ----- NPV-tulos -----
    st.markdown("## Nettonykyarvot (NPV, €)")
    col1, col2, col3 = st.columns(3)
    col1.metric("Kaukolämpö", f"{npv_kaukolampo:,.0f}")
    col2.metric("Maalämpö ilman myyntiä", f"{npv_maalampo_ilman:,.0f}")
    col3.metric("Maalämpö omaisuuden myynnillä", f"{npv_maalampo_myynnilla:,.0f}")

    # ----- Vastikkeet ensimmäiseltä vuodelta -----
    st.markdown("## Ensimmäisen vuoden vastikevertailu per m²")
    def vastike(kustannus_lista):
        vuosi_kust = kustannus_lista[0]
        return vuosi_kust / maksavat_neliot, vuosi_kust / maksavat_neliot / 12

    k_vuosi, k_kk = vastike(kaukolampo)
    m_ilman_vuosi, m_ilman_kk = vastike(maalampo_ilman)
    m_myynn_vuosi, m_myynn_kk = vastike(maalampo_myynnilla)

    st.markdown(f"**Kaukolämpö:** {k_vuosi:.2f} €/m²/v | {k_kk:.2f} €/m²/kk")
    st.markdown(f"**Maalämpö ilman omaisuuden myyntiä:** {m_ilman_vuosi:.2f} €/m²/v | {m_ilman_kk:.2f} €/m²/kk")
    st.markdown(f"**Maalämpö omaisuuden myynnillä:** {m_myynn_vuosi:.2f} €/m²/v | {m_myynn_kk:.2f} €/m²/kk")

    st.markdown("---")
    st.markdown(f"**Erotus (kaukolämpö vs maalämpö ilman myyntiä, 1. vuosi): {k_vuosi - m_ilman_vuosi:+.2f} €/m²/v**")
    st.markdown(f"**Erotus (kaukolämpö vs maalämpö myynnillä, 1. vuosi): {k_vuosi - m_myynn_vuosi:+.2f} €/m²/v**")

if __name__ == "__main__":
    main()
