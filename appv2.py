import streamlit as st
import pandas as pd
import plotly.express as px

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="Master BI", layout="wide")

# ==================================================
# SESSION DEFAULTS
# ==================================================
if "logged" not in st.session_state:
    st.session_state.logged = False

for k, v in {
    "f_corretor": "Todos",
    "f_mes": "Todos",
    "f_ano": "Todos"
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ==================================================
# CONSTANTES
# ==================================================
ORDEM_MESES = [
    "jan", "fev", "mar", "abr", "mai", "jun",
    "jul", "ago", "set", "out", "nov", "dez"
]

# ==================================================
# HELPERS
# ==================================================
def format_brl(valor):
    return f"R$ {valor:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

def limpar_filtros():
    st.session_state.f_corretor = "Todos"
    st.session_state.f_mes = "Todos"
    st.session_state.f_ano = "Todos"

# ==================================================
# LOGIN
# ==================================================
def login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            "<h2 style='text-align:center;'> Bem-vindo ao <b>Master BI</b></h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center; color:#9ca3af;'>Faça login para acessar o painel</p>",
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        user = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Entrar", use_container_width=True):
            if user and password:
                st.session_state.logged = True
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos")

# ==================================================
# DASHBOARD
# ==================================================
def dashboard():
    st.markdown(f"## Bem-vindo de volta, **{st.session_state.user}**")
    st.caption("Visão geral do desempenho comercial")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📤 Envie sua base de dados",
        type=["xlsx"]
    )

    if uploaded_file is None:
        st.info("Envie um Excel para visualizar o dashboard")
        return

    # ---------------- BASE ----------------
    df_base = pd.read_excel(uploaded_file).fillna(0)
    df_base["mes"] = df_base["mes"].str.lower()

    # ---------------- SIDEBAR ----------------
    with st.sidebar:
        st.markdown("## Master BI")
        st.markdown("---")
        st.markdown("Filtros")

        st.selectbox(
            "Corretor",
            ["Todos"] + sorted(df_base["vendedor"].unique()),
            key="f_corretor"
        )

        st.selectbox(
            "Mês",
            ["Todos"] + ORDEM_MESES,
            key="f_mes"
        )

        st.selectbox(
            "Ano",
            ["Todos"] + sorted(df_base["ano"].astype(str).unique()),
            key="f_ano"
        )

        st.button(
            "Limpar filtros",
            use_container_width=True,
            on_click=limpar_filtros
        )

        st.markdown("---")
        st.markdown(f"👤 **{st.session_state.user}**")

        if st.button("Sair", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ---------------- APLICA FILTROS ----------------
    df = df_base.copy()

    if st.session_state.f_corretor != "Todos":
        df = df[df["vendedor"] == st.session_state.f_corretor]

    if st.session_state.f_mes != "Todos":
        df = df[df["mes"] == st.session_state.f_mes]

    if st.session_state.f_ano != "Todos":
        df = df[df["ano"].astype(str) == st.session_state.f_ano]

    if df.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        return

    # ---------------- KPIs ----------------
    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Faturamento", format_brl(df["faturamento"].sum()))
    k2.metric("Vendas", (df["tipo"] == "Venda").sum())
    k3.metric("Locações", (df["tipo"] == "Locação").sum())
    k4.metric("Conversão", f"{round(df['conversao'].mean()*100,1)}%")

    st.markdown("---")

    # ---------------- GRÁFICO ----------------
    fig = px.bar(
        df,
        x="mes",
        y="faturamento",
        color="tipo",
        barmode="group",
        title="Faturamento por Vendas e Locações",
        category_orders={"mes": ORDEM_MESES}
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # ---------------- TABELA CORRETORES ----------------
    st.markdown("### 📋 Desempenho por Corretor")

    tabela = df.groupby("vendedor").agg(
        faturamento=("faturamento", "sum"),
        conversao=("conversao", "mean")
    ).reset_index()

    tabela.columns = ["Corretor", "Faturamento", "Conversão (%)"]
    tabela["Faturamento"] = tabela["Faturamento"].apply(format_brl)
    tabela["Conversão (%)"] = (tabela["Conversão (%)"] * 100).round(1)

    st.dataframe(tabela, use_container_width=True)

# ==================================================
# RENDER
# ==================================================
if not st.session_state.logged:
    login()
else:
    dashboard()



