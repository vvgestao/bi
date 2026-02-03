import streamlit as st
import pandas as pd
import plotly.express as px
import json

# --------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# --------------------------------------------------
st.set_page_config(
    page_title="Vendas e Locações Imobiliárias",
    layout="wide"
)

# --------------------------------------------------
# FUNÇÕES AUXILIARES
# --------------------------------------------------
def load_users():
    try:
        users = pd.read_csv("users.csv", sep=",")
    except:
        users = pd.read_csv("users.csv", sep=";")

    users.columns = (
        users.columns
        .str.strip()
        .str.lower()
        .str.replace("á", "a")
        .str.replace("ã", "a")
        .str.replace("ç", "c")
    )
    return users

def save_users(users):
    users.to_csv("users.csv", index=False)

def logout():
    st.session_state.clear()
    st.rerun()

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
def login():
    users = load_users()

    st.title("🔐 Acesso ao Portal")

    user_input = st.text_input("Usuário")
    password_input = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        valid = users[
            (users["user"].astype(str) == user_input) &
            (users["password"].astype(str) == password_input)
        ]

        if not valid.empty:
            st.session_state["logged"] = True
            st.session_state["user"] = user_input
            st.success("Login realizado com sucesso")
            st.rerun()
        else:
            st.error("Usuário ou senha inválidos")

# --------------------------------------------------
# ALTERAR SENHA
# --------------------------------------------------
def change_password():
    users = load_users()
    user = st.session_state["user"]

    st.subheader("🔐 Alterar senha")

    senha_atual = st.text_input("Senha atual", type="password")
    nova_senha = st.text_input("Nova senha", type="password")
    confirmar = st.text_input("Confirmar nova senha", type="password")

    if st.button("Atualizar senha"):
        senha_real = users.loc[users["user"] == user, "password"].values[0]

        if senha_atual != senha_real:
            st.error("Senha atual incorreta")
            return

        if nova_senha != confirmar:
            st.error("As senhas não coincidem")
            return

        users.loc[users["user"] == user, "password"] = nova_senha
        save_users(users)

        st.success("Senha atualizada com sucesso")
        st.info("Faça login novamente")
        logout()

# --------------------------------------------------
# DASHBOARD
# --------------------------------------------------
def dashboard():
    # TOPO COM LOGOUT
    col_title, col_logout = st.columns([8,1])

    with col_title:
        st.markdown("## 📊 Vendas e Locações Imobiliárias")

    with col_logout:
        st.button("🚪 Sair", on_click=logout)

    st.markdown("---")

    # OPÇÃO ALTERAR SENHA
    with st.expander("🔐 Alterar senha"):
        change_password()

    # UPLOAD DO EXCEL
    uploaded_file = st.file_uploader(
        "📤 Envie o Excel padrão",
        type=["xlsx"]
    )

    if uploaded_file is None:
        st.info("Envie o Excel para visualizar o dashboard")
        return

    df = pd.read_excel(uploaded_file)

    # --------------------------------------------------
    # FILTROS
    # --------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        vendedor = st.selectbox(
            "Vendedor",
            ["Todos"] + sorted(df["vendedor"].unique())
        )

    with col2:
        mes = st.selectbox(
            "Mês",
            ["Todos"] + sorted(df["mes"].unique())
        )

    with col3:
        ano = st.selectbox(
            "Ano",
            sorted(df["ano"].unique())
        )

    if vendedor != "Todos":
        df = df[df["vendedor"] == vendedor]

    if mes != "Todos":
        df = df[df["mes"] == mes]

    df = df[df["ano"] == ano]

    # --------------------------------------------------
    # KPIs
    # --------------------------------------------------
    faturamento = df["faturamento"].sum()
    tempo_medio = int(df["tempo_fechamento"].mean())
    visitas = round(df["visitas"].mean(), 1)
    conversao = round(df["conversao"].mean() * 100, 1)

    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Faturamento Bruto", f"R$ {faturamento:,.0f}".replace(",", "."))
    k2.metric("Tempo Médio até fechamento", f"{tempo_medio} dias")
    k3.metric("Nº médio de visitas", visitas)
    k4.metric("Taxa de conversão", f"{conversao}%")

    st.markdown("---")

    # --------------------------------------------------
    # GRÁFICOS
    # --------------------------------------------------
    g1, g2, g3 = st.columns([1, 2, 1])

    with g1:
        venda = df[df["tipo"] == "Venda"].shape[0]
        locacao = df[df["tipo"] == "Locação"].shape[0]

        fig_donut = px.pie(
            names=["Venda", "Locação"],
            values=[venda, locacao],
            hole=0.7
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with g2:
        fig_bar = px.bar(
            df,
            x="mes",
            y="faturamento",
            color="tipo",
            barmode="group"
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with g3:
        with open("brazil_states.geojson", encoding="utf-8") as f:
            geojson = json.load(f)

        df_map = df.groupby("uf", as_index=False).agg(
            faturamento=("faturamento", "sum")
        )

        fig_map = px.choropleth(
            df_map,
            geojson=geojson,
            locations="uf",
            featureidkey="properties.sigla",
            color="faturamento",
            color_continuous_scale="Blues",
            scope="south america",
            title="Faturamento por UF"
        )

        fig_map.update_geos(fitbounds="locations", visible=False)
        st.plotly_chart(fig_map, use_container_width=True)

# --------------------------------------------------
# CONTROLE DE SESSÃO
# --------------------------------------------------
if "logged" not in st.session_state:
    st.session_state["logged"] = False

if not st.session_state["logged"]:
    login()
else:
    dashboard()
