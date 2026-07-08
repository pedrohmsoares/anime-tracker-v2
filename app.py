import streamlit as st
import json
import os
import requests # NOVO: Biblioteca para consumir a API do AniList
from datetime import datetime, date

ARQUIVO_DADOS = 'meus_animes.json'

def carregar_dados():
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"animes": {}}

def salvar_dados(dados):
    with open(ARQUIVO_DADOS, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def classificar_nota(nota):
    if nota >= 9.0: return "⭐⭐⭐⭐⭐ Obra-prima!"
    elif nota >= 7.5: return "⭐⭐⭐⭐ Excelente!"
    elif nota >= 6.0: return "⭐⭐⭐ Bom"
    elif nota >= 4.0: return "⭐⭐ Mediano"
    else: return "⭐ Ruim"

def ler_data(data_str):
    if data_str:
        try:
            return datetime.strptime(data_str, "%Y-%m-%d").date()
        except:
            return None
    return None

def formatar_data(data_str):
    if not data_str: return ""
    try:
        d = datetime.strptime(data_str, "%Y-%m-%d")
        return d.strftime("%d/%m/%Y")
    except:
        return data_str
    
def calcular_media_anime(anime_dict):
    resenhas = anime_dict.get("resenhas", {})
    if not resenhas:
        return None
    soma = 0
    for notas in resenhas.values():
        soma += (notas.get("historia", 5.0) + notas.get("animacao", 5.0) + notas.get("personagens", 5.0) + notas.get("worldbuilding", 5.0) + notas.get("direcao", 5.0) + notas.get("diversao", 5.0)) / 6
    return soma / len(resenhas)

# --- NOVIDADE: FUNÇÃO DA API DO ANILIST (ATUALIZADA) ---
def buscar_anime_anilist(termo):
    url = 'https://graphql.anilist.co'
    query = '''
    query ($search: String) {
      Page(page: 1, perPage: 10) {
        media(search: $search, type: ANIME) {
          id
          title { romaji english }
          coverImage { large }
          episodes
          nextAiringEpisode { episode } 
        }
      }
    }
    '''
    variables = {'search': termo}
    try:
        response = requests.post(url, json={'query': query, 'variables': variables})
        if response.status_code == 200:
            return response.json()['data']['Page']['media']
    except Exception as e:
        st.error(f"Erro ao conectar com AniList: {e}")
    return []

hoje = date.today()

st.set_page_config(page_title="Anime Tracker Visual", page_icon="🎌", layout="centered")

# --- GERENCIAMENTO DE ESTADO (MEMÓRIA) ---
if 'anime_em_destaque' not in st.session_state:
    st.session_state.anime_em_destaque = None
if 'resultados_busca' not in st.session_state:
    st.session_state.resultados_busca = []
if 'form_nome' not in st.session_state:
    st.session_state.form_nome = ""
if 'form_capa' not in st.session_state:
    st.session_state.form_capa = ""
if 'form_eps' not in st.session_state:
    st.session_state.form_eps = 1

st.markdown("""
<style>
    .capa-grade { transition: transform 0.2s; }
    .capa-grade:hover { transform: scale(1.02); }
    .img-grade { width: 100%; aspect-ratio: 2 / 3; object-fit: cover; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }
    .img-progresso { width: 250px; aspect-ratio: 2 / 3; object-fit: cover; border-radius: 10px; box-shadow: 0 4px 8px rgba(0,0,0,0.2); margin-bottom: 20px; }
    .img-miniatura { width: 100%; aspect-ratio: 16 / 9; object-fit: cover; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .wallpaper-saga { border-radius: 5px; margin-bottom: 10px; object-fit: cover; max-height: 250px; }
    .anilist-card { display: flex; align-items: center; gap: 15px; margin-bottom: 10px; padding: 10px; border-radius: 8px; background-color: rgba(255,255,255,0.05); }
    .container-capa { position: relative; display: inline-block; width: 100%; }
    .badge-nota { position: absolute; top: 8px; right: 8px; background-color: rgba(0,0,0,0.85); color: #FFD700; padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.5); z-index: 10; border: 1px solid #FFD700; }
</style>
""", unsafe_allow_html=True)

st.title("🎌 Meu Tracker de Animes")

dados = carregar_dados()

aba_progresso, aba_adicionar, aba_editar, aba_resenhas, aba_resumo = st.tabs([
    "📺 Progresso", "➕ Adicionar", "✏️ Editar", "📝 Resenhas", "📊 Visão Geral"
])

# --- TELA 1: MEU PROGRESSO ---
with aba_progresso:
    st.header("Atualizar Episódio")
    if not dados["animes"]:
        st.info("Nenhum anime cadastrado ainda.")
    else:
        espaco_capa_progresso = st.empty()
        anime_selecionado = st.selectbox("Selecione o Anime", list(dados["animes"].keys()), key="prog_anime")
        anime_info = dados["animes"][anime_selecionado]
        
        if anime_info.get("capa_url"):
            espaco_capa_progresso.markdown(f'<div><img src="{anime_info["capa_url"]}" class="img-progresso"></div>', unsafe_allow_html=True)
        
        ep_atual = anime_info.get("ep_atual", 0)
        total = anime_info.get("total_eps", 1)
        
        arco_atual_nome = None
        arco_atual_imagem = None
        ep_inicio_atual = None
        ep_fim_atual = None
        indice_arco_atual = -1
        
        for i, arco in enumerate(anime_info.get("arcos", [])):
            if isinstance(arco, dict):
                ep_inicio = arco.get("ep_inicio")
                ep_fim = arco.get("ep_fim")
                if ep_inicio is not None and ep_fim is not None:
                    if ep_inicio <= ep_atual <= ep_fim:
                        arco_atual_nome = arco["nome"]
                        arco_atual_imagem = arco.get("imagem_arco")
                        ep_inicio_atual = ep_inicio
                        ep_fim_atual = ep_fim
                        indice_arco_atual = i
                        break
        
        if arco_atual_nome:
            st.markdown("### 📍 Você está no arco:")
            col_img, col_txt = st.columns([1, 4])
            with col_img:
                if arco_atual_imagem:
                    st.markdown(f'<img src="{arco_atual_imagem}" class="img-miniatura">', unsafe_allow_html=True)
            with col_txt:
                st.markdown(f"<h4 style='margin-top: 5px; margin-bottom: 0px;'>{arco_atual_nome}</h4>", unsafe_allow_html=True)
                
                # --- NOVIDADE: Faltam eps ---
                faltam_arco = ep_fim_atual - ep_atual
                texto_faltam = f" — **Faltam {faltam_arco} eps**" if faltam_arco > 0 else " — **Arco finalizado!**"
                st.caption(f"**Episódios:** {ep_inicio_atual} a {ep_fim_atual} ({ep_fim_atual - ep_inicio_atual + 1} eps){texto_faltam}")
            st.write("") 
        
        st.write(f"**Progresso atual:** {ep_atual} / {total}")
        st.progress(min(ep_atual / total if total > 0 else 0, 1.0))
        
        novo_ep = st.number_input("Estou no episódio:", min_value=0, max_value=total, value=ep_atual, step=1)
        if st.button("Atualizar Progresso"):
            dados["animes"][anime_selecionado]["ep_atual"] = novo_ep
            salvar_dados(dados)
            st.success("Progresso atualizado!")
            st.rerun()

        # --- DIÁRIO DE DATAS ---
        st.divider()
        st.markdown("### 📅 Diário de Bordo (Datas)")
        
        saga_atual_nome = None
        if arco_atual_nome and indice_arco_atual != -1:
            saga_atual_nome = anime_info["arcos"][indice_arco_atual].get("saga")

        with st.form("form_datas"):
            st.caption("Registre quando você começou e terminou:")
            
            st.markdown(f"**Anime: {anime_selecionado}**")
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                dt_ini_anime = st.date_input("Início (Anime)", value=ler_data(anime_info.get("data_inicio")) or hoje, format="DD/MM/YYYY")
            with col_a2:
                check_fim_anime = st.checkbox("Já terminei o anime", value=bool(anime_info.get("data_fim")))
                if check_fim_anime:
                    dt_fim_anime = st.date_input("Fim (Anime)", value=ler_data(anime_info.get("data_fim")) or hoje, format="DD/MM/YYYY")
                else:
                    dt_fim_anime = None
            st.write("")
            
            dt_ini_saga, dt_fim_saga = None, None
            if saga_atual_nome and saga_atual_nome != "Sem Saga":
                st.markdown(f"**Saga: {saga_atual_nome}**")
                sagas_ini, sagas_fim = anime_info.get("sagas_datas", {}), anime_info.get("sagas_datas_fim", {})
                
                col_s1, col_s2 = st.columns(2)
                with col_s1:
                    dt_ini_saga = st.date_input("Início (Saga)", value=ler_data(sagas_ini.get(saga_atual_nome)) or hoje, format="DD/MM/YYYY")
                with col_s2:
                    check_fim_saga = st.checkbox("Já terminei a saga", value=bool(sagas_fim.get(saga_atual_nome)))
                    if check_fim_saga:
                        dt_fim_saga = st.date_input("Fim (Saga)", value=ler_data(sagas_fim.get(saga_atual_nome)) or hoje, format="DD/MM/YYYY")
                    else:
                        dt_fim_saga = None
                st.write("")
            
            dt_ini_arco, dt_fim_arco = None, None
            if arco_atual_nome and indice_arco_atual != -1:
                st.markdown(f"**Arco: {arco_atual_nome}**")
                arco_dict = anime_info["arcos"][indice_arco_atual]
                
                col_ar1, col_ar2 = st.columns(2)
                with col_ar1:
                    dt_ini_arco = st.date_input("Início (Arco)", value=ler_data(arco_dict.get("data_inicio")) or hoje, format="DD/MM/YYYY")
                with col_ar2:
                    check_fim_arco = st.checkbox("Já terminei o arco", value=bool(arco_dict.get("data_fim")))
                    if check_fim_arco:
                        dt_fim_arco = st.date_input("Fim (Arco)", value=ler_data(arco_dict.get("data_fim")) or hoje, format="DD/MM/YYYY")
                    else:
                        dt_fim_arco = None

            if st.form_submit_button("💾 Salvar Datas"):
                dados["animes"][anime_selecionado]["data_inicio"] = dt_ini_anime.strftime("%Y-%m-%d")
                if dt_fim_anime: dados["animes"][anime_selecionado]["data_fim"] = dt_fim_anime.strftime("%Y-%m-%d")
                else: dados["animes"][anime_selecionado].pop("data_fim", None)
                    
                if saga_atual_nome and saga_atual_nome != "Sem Saga":
                    if "sagas_datas" not in dados["animes"][anime_selecionado]: dados["animes"][anime_selecionado]["sagas_datas"] = {}
                    if "sagas_datas_fim" not in dados["animes"][anime_selecionado]: dados["animes"][anime_selecionado]["sagas_datas_fim"] = {}
                    dados["animes"][anime_selecionado]["sagas_datas"][saga_atual_nome] = dt_ini_saga.strftime("%Y-%m-%d")
                    if dt_fim_saga: dados["animes"][anime_selecionado]["sagas_datas_fim"][saga_atual_nome] = dt_fim_saga.strftime("%Y-%m-%d")
                    else: dados["animes"][anime_selecionado]["sagas_datas_fim"].pop(saga_atual_nome, None)

                if arco_atual_nome and indice_arco_atual != -1:
                    dados["animes"][anime_selecionado]["arcos"][indice_arco_atual]["data_inicio"] = dt_ini_arco.strftime("%Y-%m-%d")
                    if dt_fim_arco: dados["animes"][anime_selecionado]["arcos"][indice_arco_atual]["data_fim"] = dt_fim_arco.strftime("%Y-%m-%d")
                    else: dados["animes"][anime_selecionado]["arcos"][indice_arco_atual].pop("data_fim", None)
                        
                salvar_dados(dados)
                st.success("Datas registradas com sucesso no seu Diário!")
                st.rerun()

# --- TELA 2: ADICIONAR ANIME (INTEGRAÇÃO ANILIST) ---
with aba_adicionar:
    st.header("Adicionar Novo Anime")
    
    st.subheader("🔍 Buscar na API (AniList)")
    col_busca, col_btn = st.columns([4, 1])
    with col_busca:
        termo_busca = st.text_input("Nome do Anime (em inglês ou romaji)", placeholder="Ex: One Piece, Jujutsu Kaisen...")
    with col_btn:
        st.write("") # Espaçamento
        st.write("")
        if st.button("Buscar", use_container_width=True):
            if termo_busca:
                with st.spinner("Buscando no AniList..."):
                    st.session_state.resultados_busca = buscar_anime_anilist(termo_busca)
                    
    if st.session_state.resultados_busca:
        st.write("Resultados encontrados:")
        for anime in st.session_state.resultados_busca:
            titulo = anime['title'].get('english') or anime['title'].get('romaji')
            capa = anime['coverImage']['large']
            
            # --- LÓGICA CORRIGIDA PARA ANIMES EM LANÇAMENTO (COMO ONE PIECE) ---
            eps = anime.get('episodes')
            if not eps: # Se o total for vazio (null), o anime ainda está lançando
                next_airing = anime.get('nextAiringEpisode')
                if next_airing and next_airing.get('episode'):
                    # Pega o próximo episódio a lançar e subtrai 1 para saber o total atual
                    eps = next_airing.get('episode') - 1
                else:
                    eps = 1 # Fallback de segurança
            # -------------------------------------------------------------------
            
            with st.container():
                st.markdown(f'''
                <div class="anilist-card">
                    <img src="{capa}" width="50" style="border-radius: 5px;">
                    <div>
                        <strong>{titulo}</strong><br>
                        <small>{eps} episódios</small>
                    </div>
                </div>
                ''', unsafe_allow_html=True)
                if st.button(f"Usar '{titulo}'", key=f"usar_{anime['id']}"):
                    st.session_state.form_nome = titulo
                    st.session_state.form_capa = capa
                    st.session_state.form_eps = eps
                    st.session_state.resultados_busca = [] # Limpa a busca
                    st.rerun()
                    
    st.divider()
    st.subheader("📝 Preenchimento Manual / Estrutura")
    
    with st.form("form_novo_anime", clear_on_submit=True):
        nome = st.text_input("Nome do Anime", value=st.session_state.form_nome)
        capa_url = st.text_input("URL da Imagem de Capa", value=st.session_state.form_capa)
        total_eps = st.number_input("Total de Episódios", min_value=1, step=1, value=st.session_state.form_eps)
        
        usa_sagas = st.checkbox("Este anime é dividido em Sagas?")
        st.caption("Formato para Arcos: `Nome | URL da Imagem | Episódios (Ex: 1-10)`")
        arcos_str = st.text_area("Estrutura da História", height=200)
        submit = st.form_submit_button("Salvar Anime no Tracker")
        
        if submit and nome:
            if nome in dados["animes"]:
                st.error("Esse anime já está cadastrado!")
            else:
                arcos_lista, saga_imagens, saga_atual = [], {}, "Sem Saga"
                for linha in arcos_str.split('\n'):
                    linha = linha.strip()
                    if not linha: continue
                    partes = [p.strip() for p in linha.split('|')]
                    nome_item = partes[0]
                    url_item, eps_item = None, None
                    if len(partes) == 2:
                        if '-' in partes[1] and partes[1].replace('-', '').strip().isdigit(): eps_item = partes[1]
                        else: url_item = partes[1] if partes[1] else None
                    elif len(partes) >= 3:
                        url_item = partes[1] if partes[1].strip() else None
                        eps_item = partes[2]
                        
                    if usa_sagas and not nome_item.startswith('-'):
                        saga_atual = nome_item
                        if url_item: saga_imagens[saga_atual] = url_item
                    else:
                        nome_arco = nome_item.lstrip('- ').strip()
                        ep_inicio, ep_fim = None, None
                        if eps_item and '-' in eps_item:
                            try:
                                inicio, fim = eps_item.split('-')
                                ep_inicio, ep_fim = int(inicio.strip()), int(fim.strip())
                            except ValueError: pass
                        arcos_lista.append({
                            "nome": nome_arco, "saga": saga_atual if usa_sagas else None,
                            "imagem_arco": url_item, "ep_inicio": ep_inicio, "ep_fim": ep_fim
                        })
                dados["animes"][nome] = {
                    "capa_url": capa_url, "total_eps": total_eps, "ep_atual": 0,
                    "usa_sagas": usa_sagas, "saga_imagens": saga_imagens, "arcos": arcos_lista, "resenhas": {}
                }
                salvar_dados(dados)
                st.session_state.form_nome, st.session_state.form_capa, st.session_state.form_eps = "", "", 1
                st.success(f"Anime '{nome}' adicionado com sucesso!")
                st.rerun()

# --- TELA 3: EDITAR ANIME ---
with aba_editar:
    st.header("Editar ou Remover Anime")
    if not dados["animes"]:
        st.info("Nenhum anime cadastrado para editar.")
    else:
        anime_para_editar = st.selectbox("Selecione o Anime para editar", list(dados["animes"].keys()), key="edit_anime")
        anime_info = dados["animes"][anime_para_editar]
        
        # --- NOVIDADE: EXIBIÇÃO DA CAPA NA EDIÇÃO ---
        if anime_info.get("capa_url"):
            st.markdown(f'<div><img src="{anime_info["capa_url"]}" class="img-progresso"></div>', unsafe_allow_html=True)
        # -------------------------------------------
        
        usa_sagas_atual = anime_info.get("usa_sagas", False)
        saga_imagens_atuais = anime_info.get("saga_imagens", {})
        
        linhas_texto = []
        saga_temp = None
        for arco in anime_info.get("arcos", []):
            if isinstance(arco, dict):
                nome_arco, saga_arco = arco["nome"], arco["saga"]
                url_arco, ep_inicio, ep_fim = arco.get("imagem_arco"), arco.get("ep_inicio"), arco.get("ep_fim")
                if usa_sagas_atual and saga_arco != saga_temp:
                    if saga_arco:
                        url_saga = saga_imagens_atuais.get(saga_arco)
                        linhas_texto.append(f"{saga_arco} | {url_saga}" if url_saga else saga_arco)
                    saga_temp = saga_arco
                texto_arco = f"- {nome_arco}"
                if url_arco and ep_inicio is not None: texto_arco += f" | {url_arco} | {ep_inicio}-{ep_fim}"
                elif url_arco: texto_arco += f" | {url_arco}"
                elif ep_inicio is not None: texto_arco += f" | {ep_inicio}-{ep_fim}"
                linhas_texto.append(texto_arco)
            else: linhas_texto.append(arco)
                
        arcos_atuais_str = "\n".join(linhas_texto)
        with st.form("form_editar_anime"):
            novo_nome = st.text_input("Nome do Anime", value=anime_para_editar)
            novo_capa_url = st.text_input("URL da Imagem de Capa", value=anime_info.get("capa_url", ""))
            novo_total_eps = st.number_input("Total de Episódios", min_value=1, step=1, value=anime_info.get("total_eps", 1))
            usa_sagas_edit = st.checkbox("Dividido em Sagas?", value=usa_sagas_atual)
            novos_arcos_str = st.text_area("Estrutura da História", value=arcos_atuais_str, height=250)
            submit_edit = st.form_submit_button("Salvar Alterações")
            
            if submit_edit:
                novos_arcos_lista, novas_saga_imagens, saga_atual = [], {}, "Sem Saga"
                for linha in novos_arcos_str.split('\n'):
                    linha = linha.strip()
                    if not linha: continue
                    partes = [p.strip() for p in linha.split('|')]
                    nome_item, url_item, eps_item = partes[0], None, None
                    if len(partes) == 2:
                        if '-' in partes[1] and partes[1].replace('-', '').strip().isdigit(): eps_item = partes[1]
                        else: url_item = partes[1] if partes[1] else None
                    elif len(partes) >= 3:
                        url_item = partes[1] if partes[1].strip() else None
                        eps_item = partes[2]
                    
                    if usa_sagas_edit and not nome_item.startswith('-'):
                        saga_atual = nome_item
                        if url_item: novas_saga_imagens[saga_atual] = url_item
                    else:
                        nome_arco = nome_item.lstrip('- ').strip()
                        ep_inicio, ep_fim = None, None
                        if eps_item and '-' in eps_item:
                            try:
                                inicio, fim = eps_item.split('-')
                                ep_inicio, ep_fim = int(inicio.strip()), int(fim.strip())
                            except ValueError: pass
                        
                        arco_antigo = next((a for a in anime_info.get("arcos", []) if isinstance(a, dict) and a["nome"] == nome_arco), {})
                        novos_arcos_lista.append({
                            "nome": nome_arco, "saga": saga_atual if usa_sagas_edit else None,
                            "imagem_arco": url_item, "ep_inicio": ep_inicio, "ep_fim": ep_fim,
                            "data_inicio": arco_antigo.get("data_inicio"), "data_fim": arco_antigo.get("data_fim")
                        })
                
                dados_preservados = dados["animes"].pop(anime_para_editar)
                dados_preservados["capa_url"], dados_preservados["total_eps"] = novo_capa_url, novo_total_eps
                dados_preservados["usa_sagas"], dados_preservados["saga_imagens"] = usa_sagas_edit, novas_saga_imagens
                dados_preservados["arcos"] = novos_arcos_lista
                
                dados["animes"][novo_nome] = dados_preservados
                salvar_dados(dados)
                if st.session_state.anime_em_destaque == anime_para_editar:
                    st.session_state.anime_em_destaque = novo_nome
                st.success("Alterações salvas!")
                st.rerun()
                
        st.divider()
        if st.button(f"🗑️ Excluir '{anime_para_editar}'", type="primary"):
            del dados["animes"][anime_para_editar]
            salvar_dados(dados)
            if st.session_state.anime_em_destaque == anime_para_editar:
                st.session_state.anime_em_destaque = None
            st.rerun()

# --- TELA 4: RESENHAS E NOTAS ---
with aba_resenhas:
    st.header("Resenhas por Arco")
    if not dados["animes"]:
        st.info("Cadastre um anime primeiro.")
    else:
        anime_resenha = st.selectbox("Selecione o Anime", list(dados["animes"].keys()), key="resenha_anime")
        lista_arcos_bruta = dados["animes"][anime_resenha].get("arcos", [])
        nomes_arcos = [a["nome"] if isinstance(a, dict) else a for a in lista_arcos_bruta]
        if not nomes_arcos:
            st.warning("Este anime não possui arcos cadastrados.")
        else:
            arco_selecionado = st.selectbox("Selecione o Arco", nomes_arcos)
            resenhas_existentes = dados["animes"][anime_resenha].get("resenhas", {})
            resenha_atual = resenhas_existentes.get(arco_selecionado, {})
            col1, col2 = st.columns(2)
            with col1:
                nota_historia = st.slider("História e Roteiro", 0.0, 10.0, float(resenha_atual.get("historia", 5.0)), step=0.5)
                nota_animacao = st.slider("Animação e Arte", 0.0, 10.0, float(resenha_atual.get("animacao", 5.0)), step=0.5)
                nota_personagens = st.slider("Personagens", 0.0, 10.0, float(resenha_atual.get("personagens", 5.0)), step=0.5)
            with col2:
                nota_world = st.slider("Worldbuilding", 0.0, 10.0, float(resenha_atual.get("worldbuilding", 5.0)), step=0.5)
                nota_direcao = st.slider("Direção", 0.0, 10.0, float(resenha_atual.get("direcao", 5.0)), step=0.5)
                nota_diversao = st.slider("Fator Pessoal (Diversão)", 0.0, 10.0, float(resenha_atual.get("diversao", 5.0)), step=0.5)
            texto_resenha = st.text_area("Sua resenha", resenha_atual.get("texto", ""), height=150)
            
            if st.button("Salvar Resenha"):
                dados["animes"][anime_resenha]["resenhas"][arco_selecionado] = {
                    "historia": nota_historia, "animacao": nota_animacao, "personagens": nota_personagens,
                    "worldbuilding": nota_world, "direcao": nota_direcao, "diversao": nota_diversao, "texto": texto_resenha
                }
                salvar_dados(dados)
                st.success("Resenha salva!")

# --- TELA 5: VISÃO GERAL ---
with aba_resumo:
    if st.session_state.anime_em_destaque not in dados["animes"]:
        st.session_state.anime_em_destaque = None

    if not dados["animes"]:
        st.header("📊 Galeria de Animes")
        st.info("Sua galeria está vazia. Cadastre um anime na aba 'Adicionar'.")
    elif st.session_state.anime_em_destaque is None:
        st.header("🎬 Minha Galeria")
        lista_de_animes = list(dados["animes"].keys())
        colunas_por_linha = 3 
        for i in range(0, len(lista_de_animes), colunas_por_linha):
            cols = st.columns(colunas_por_linha)
            for j in range(colunas_por_linha):
                if i + j < len(lista_de_animes):
                    nome_anime = lista_de_animes[i + j]
                    anime_data = dados["animes"][nome_anime]
                    capa_anime = anime_data.get("capa_url")
                    
                    # --- NOVIDADE: Calcula a média e desenha o selo ---
                    media = calcular_media_anime(anime_data)
                    badge = f'<div class="badge-nota">⭐ {media:.1f}</div>' if media else ''
                    
                    with cols[j]:
                        if capa_anime:
                            st.markdown(f'<div class="capa-grade container-capa">{badge}<img src="{capa_anime}" class="img-grade"></div>', unsafe_allow_html=True)
                        else:
                            img_placeholder = f"https://via.placeholder.com/300x450.png?text={nome_anime.replace(' ', '+')}"
                            st.markdown(f'<div class="capa-grade container-capa">{badge}<img src="{img_placeholder}" class="img-grade"></div>', unsafe_allow_html=True)
                        if st.button(f"Abrir {nome_anime}", key=f"btn_{nome_anime}", use_container_width=True):
                            st.session_state.anime_em_destaque = nome_anime
                            st.rerun()
    else:
        anime_aberto = st.session_state.anime_em_destaque
        if st.button("⬅️ Voltar para a Galeria"):
            st.session_state.anime_em_destaque = None
            st.rerun()
            
        st.divider()
        st.header(f"📊 Resumo: {anime_aberto}")
        
        anime = dados["animes"][anime_aberto]
        
        # --- NOVIDADE: Selo grande na visão detalhada ---
        media_detalhe = calcular_media_anime(anime)
        badge_detalhe = f'<div class="badge-nota" style="font-size: 16px; top: 12px; right: 12px;">⭐ {media_detalhe:.1f}</div>' if media_detalhe else ''
        
        if anime.get("capa_url"):
            st.markdown(f'<div class="container-capa" style="width: 250px;">{badge_detalhe}<img src="{anime["capa_url"]}" class="img-progresso"></div>', unsafe_allow_html=True)
            
        data_ini_anime = anime.get("data_inicio")
        data_fim_anime = anime.get("data_fim")
        if data_ini_anime and data_fim_anime:
            st.markdown(f"**📅 Período:** {formatar_data(data_ini_anime)} a {formatar_data(data_fim_anime)}")
        elif data_ini_anime:
            st.markdown(f"**📅 Iniciado em:** {formatar_data(data_ini_anime)}")
            
        ep_atual = anime.get("ep_atual", 0)
        arco_atual_nome = None
        ep_inicio_atual, ep_fim_atual = None, None
        
        for arco in anime.get("arcos", []):
            if isinstance(arco, dict):
                ep_inicio, ep_fim = arco.get("ep_inicio"), arco.get("ep_fim")
                if ep_inicio is not None and ep_fim is not None:
                    if ep_inicio <= ep_atual <= ep_fim:
                        arco_atual_nome, ep_inicio_atual, ep_fim_atual = arco["nome"], ep_inicio, ep_fim
                        break
        
        if arco_atual_nome:
            faltam_resumo = ep_fim_atual - ep_atual
            aviso_faltam = f"Faltam **{faltam_resumo}** episódios para você fechar este arco!" if faltam_resumo > 0 else "Você já completou este arco!"
            st.success(f"📍 **Status Atual:** Você está no **{arco_atual_nome}** ({ep_inicio_atual} a {ep_fim_atual}).  \n📺 Assistindo o ep {ep_atual}. {aviso_faltam}")
        else:
            st.info(f"📺 **Status Atual:** Assistindo o episódio {ep_atual} de {anime.get('total_eps', '?')}.")
        st.write("") 

        if not anime.get("usa_sagas"):
            st.info("Este anime não está dividido em sagas.")
        else:
            sagas_dict = {}
            for arco in anime.get("arcos", []):
                if isinstance(arco, dict):
                    nome_saga = arco["saga"] or "Sem Saga"
                    if nome_saga not in sagas_dict: sagas_dict[nome_saga] = []
                    sagas_dict[nome_saga].append(arco)
            
            saga_imagens = anime.get("saga_imagens", {})
            sagas_datas_ini = anime.get("sagas_datas", {})
            sagas_datas_fim = anime.get("sagas_datas_fim", {})
            
            for saga, arcos in sagas_dict.items():
                if saga in saga_imagens:
                    st.markdown(f'<img src="{saga_imagens[saga]}" class="wallpaper-saga" style="width:100%;">', unsafe_allow_html=True)
                
                eps_inicio_saga = [a.get("ep_inicio") for a in arcos if a.get("ep_inicio") is not None]
                eps_fim_saga = [a.get("ep_fim") for a in arcos if a.get("ep_fim") is not None]
                texto_eps_saga = ""
                if eps_inicio_saga and eps_fim_saga:
                    min_ep, max_ep = min(eps_inicio_saga), max(eps_fim_saga)
                    texto_eps_saga = f" 📺 (Eps {min_ep} a {max_ep})"
                
                saga_ini_atual, saga_fim_atual = sagas_datas_ini.get(saga), sagas_datas_fim.get(saga)
                
                if saga_ini_atual and saga_fim_atual: status_saga = "🟢 Completo"
                elif saga_ini_atual: status_saga = "🟡 Em progresso"
                else: status_saga = "⚪ Não iniciado"
                
                st.subheader(f"📘 {saga}{texto_eps_saga} - {status_saga}")
                
                if saga_ini_atual and saga_fim_atual: st.caption(f"📅 **Período da Saga:** {formatar_data(saga_ini_atual)} a {formatar_data(saga_fim_atual)}")
                elif saga_ini_atual: st.caption(f"📅 **Saga iniciada a:** {formatar_data(saga_ini_atual)}")
                
                notas_da_saga = []
                
                for arco_dict in arcos:
                    nome_arco, url_arco = arco_dict["nome"], arco_dict.get("imagem_arco")
                    arco_ini, arco_fim = arco_dict.get("data_inicio"), arco_dict.get("data_fim")
                    ep_ini_arco, ep_fim_arco = arco_dict.get("ep_inicio"), arco_dict.get("ep_fim")
                    
                    texto_eps_arco = ""
                    if ep_ini_arco is not None and ep_fim_arco is not None:
                        contagem = ep_fim_arco - ep_ini_arco + 1
                        texto_eps_arco = f" `[Eps {ep_ini_arco}-{ep_fim_arco} ({contagem} eps)]`"
                        
                    if arco_ini and arco_fim: status_arco = "🟢 Completo"
                    elif arco_ini: status_arco = "🟡 Em progresso"
                    else: status_arco = "⚪ Não iniciado"
                        
                    resenha = anime.get("resenhas", {}).get(nome_arco)
                    
                    col_img, col_texto = st.columns([1, 4])
                    with col_img:
                        if url_arco: st.markdown(f'<img src="{url_arco}" class="img-miniatura">', unsafe_allow_html=True)
                    
                    with col_texto:
                        if resenha:
                            n_hist, n_anim, n_pers = resenha.get("historia", 5.0), resenha.get("animacao", 5.0), resenha.get("personagens", 5.0)
                            n_worl, n_dire, n_dive = resenha.get("worldbuilding", 5.0), resenha.get("direcao", 5.0), resenha.get("diversao", 5.0)
                            media_arco = (n_hist + n_anim + n_pers + n_worl + n_dire + n_dive) / 6
                            notas_da_saga.append(media_arco)
                            
                            st.markdown(f"**{nome_arco}**{texto_eps_arco} • {status_arco}  \n⭐ **{media_arco:.1f}/10** - {classificar_nota(media_arco)}")
                            
                            if arco_ini and arco_fim: st.write(f"📅 *{formatar_data(arco_ini)} a {formatar_data(arco_fim)}*")
                            elif arco_ini: st.write(f"📅 *Desde {formatar_data(arco_ini)}*")
                                
                            texto_escrito = resenha.get("texto", "").strip()
                            if texto_escrito: st.caption(f'"{texto_escrito}"')
                        else:
                            st.markdown(f"**{nome_arco}**{texto_eps_arco} • {status_arco}  \n*(Sem avaliação)*")
                            if arco_ini and arco_fim: st.write(f"📅 *{formatar_data(arco_ini)} a {formatar_data(arco_fim)}*")
                            elif arco_ini: st.write(f"📅 *Desde {formatar_data(arco_ini)}*")
                
                if notas_da_saga:
                    media_saga = sum(notas_da_saga) / len(notas_da_saga)
                    st.markdown(f"### ⭐ Média da Saga: {media_saga:.1f}/10")
                    st.markdown(f"**Veredito:** {classificar_nota(media_saga)}")
                else:
                    st.markdown("**⭐ Média da Saga: N/A**")
                st.divider()