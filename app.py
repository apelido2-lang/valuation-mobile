import streamlit as st
import yfinance as yf
import math
import pandas as pd

# Configuração visual otimizada para telas de celulares
st.set_page_config(page_title="Valuation B3 Mobile", page_icon="📈", layout="centered")

st.title("📲 Valuation Mobile - B3")
st.caption("Métodos de Benjamin Graham, Décio Bazin, FCD e Margem de Segurança")

# Campo de entrada para a ação
ticker_input = st.text_input("Digite o Código da Ação (ex: BBAS3, PETR4, TAEE11):", value="BBAS3").strip().upper()

if ticker_input:
    # Formatação do código para padrão B3 no Yahoo Finance
    ticker_symbol = f"{ticker_input}.SA" if '.' not in ticker_input and len(ticker_input) in [5, 6] else ticker_input
    
    with st.spinner('Buscando dados em tempo real na B3...'):
        try:
            acao = yf.Ticker(ticker_symbol)
            info = acao.info
            preco_atual = info.get('currentPrice') or info.get('regularMarketPrice')
            lpa = info.get('trailingEps')
            vpa = info.get('bookValue')
        except Exception:
            preco_atual = None

    if preco_atual is None:
        st.error("Não foi possível carregar os dados desta ação. Verifique se o código está correto (ex: BBAS3, ITUB4).")
    else:
        st.metric("Preço Atual de Mercado", f"R$ {preco_atual:.2f}")
        
        tab1, tab2, tab3, tab4 = st.tabs(["🏛️ Graham", "💰 Bazin", "📊 FCD", "🛡️ Margem"])
        
        # --- TAB 1: GRAHAM ---
        with tab1:
            st.subheader("Método de Benjamin Graham")
            if lpa and vpa and lpa > 0 and vpa > 0:
                teto_graham = math.sqrt(22.5 * lpa * vpa)
                margem_g = ((teto_graham - preco_atual) / teto_graham) * 100
                st.write(f"**LPA:** R$ {lpa:.2f} | **VPA:** R$ {vpa:.2f}")
                st.success(f"**Preço-Teto (Graham):** R$ {teto_graham:.2f}")
                st.info(f"**Margem de Segurança:** {margem_g:.2f}%")
                if preco_atual <= teto_graham:
                    st.success("✅ **VALE A PENA**: Ação negociada com desconto!")
                else:
                    st.error("❌ **NÃO VALE A PENA**: Acima do preço justo de Graham.")
            else:
                st.warning("O método de Graham exige LPA e VPA positivos.")

        # --- TAB 2: BAZIN ---
        with tab2:
            st.subheader("Método Décio Bazin (Yield 6%)")
            dividendos_hist = acao.dividends
            dpa_12m = 0.0
            if not dividendos_hist.empty:
                data_hoje = pd.Timestamp.now(tz=dividendos_hist.index.tz)
                data_limite = data_hoje - pd.Timedelta(days=365)
                dividendos_12m = dividendos_hist[dividendos_hist.index >= data_limite]
                dpa_12m = float(dividendos_12m.sum())
            
            if dpa_12m > 0:
                teto_bazin = dpa_12m / 0.06
                dy_atual = (dpa_12m / preco_atual) * 100
                st.write(f"**Proventos (12M):** R$ {dpa_12m:.2f} | **DY Atual:** {dy_atual:.2f}%")
                st.success(f"**Preço-Teto (Bazin 6%):** R$ {teto_bazin:.2f}")
                if preco_atual <= teto_bazin:
                    st.success("✅ **VALE A PENA**: Garante no mínimo 6% de Dividend Yield.")
                else:
                    st.error("❌ **NÃO VALE A PENA**: Preço acima do teto para 6% DY.")
            else:
                st.warning("Empresa não registrou pagamento de dividendos nos últimos 12 meses.")

        # --- TAB 3: FCD ---
        with tab3:
            st.subheader("Fluxo de Caixa Descontado (FCD)")
            crescimento = st.slider("Crescimento Anual Estimado (1-5 anos %):", 0.0, 20.0, 8.0) / 100
            wacc = st.slider("Taxa de Desconto / WACC (%):", 5.0, 20.0, 12.0) / 100
            
            fcf_recente = info.get('freeCashflow')
            acoes = info.get('sharesOutstanding')
            
            if fcf_recente and acoes and fcf_recente > 0:
                fluxos = [fcf_recente * ((1 + crescimento) ** t) / ((1 + wacc) ** t) for t in range(1, 6)]
                perpetuidade = (fcf_recente * ((1 + crescimento)**5) * 1.035) / (wacc - 0.035)
                vp_perp = perpetuidade / ((1 + wacc) ** 5)
                
                preco_fcd = (sum(fluxos) + vp_perp) / acoes
                st.success(f"**Preço Justo FCD:** R$ {preco_fcd:.2f}")
                if preco_atual <= preco_fcd:
                    st.success("✅ **VALE A PENA**: Desconto frente às projeções.")
                else:
                    st.error("❌ **NÃO VALE A PENA**: Negociada acima das projeções.")
            else:
                st.warning("Dados de Fluxo de Caixa Livre indisponíveis para esta empresa.")

        # --- TAB 4: MARGEM DE SEGURANÇA CONSOLIDADA ---
        with tab4:
            st.subheader("Margem de Segurança Consolidada")
            margem_alvo = st.number_input("Sua Margem de Segurança Exigida (%):", value=20.0, step=1.0)
            
            tetos = []
            if lpa and vpa and lpa > 0 and vpa > 0: tetos.append(math.sqrt(22.5 * lpa * vpa))
            if dpa_12m > 0: tetos.append(dpa_12m / 0.06)
            
            if tetos:
                val_intrinseco_medio = sum(tetos) / len(tetos)
                preco_teto_seguranca = val_intrinseco_medio * (1 - (margem_alvo / 100))
                margem_real = ((val_intrinseco_medio - preco_atual) / val_intrinseco_medio) * 100
                
                st.write(f"**Valor Intrínseco Médio:** R$ {val_intrinseco_medio:.2f}")
                st.metric("Margem de Segurança Real", f"{margem_real:.2f}%")
                st.success(f"**Preço Máximo de Compra (c/ {margem_alvo:.0f}% de margem):** R$ {preco_teto_seguranca:.2f}")
            else:
                st.warning("Não foi possível calcular a consolidação para esta empresa.")
