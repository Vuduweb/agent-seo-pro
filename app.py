import streamlit as st
import anthropic
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

# Configuration de la page
st.set_page_config(
    page_title="Agent SEO Pro",
    page_icon="🚀",
    layout="wide"
)

# Style CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(120deg, #1e3a8a, #3b82f6, #06b6d4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(120deg, #3b82f6, #06b6d4);
        color: white;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de la session
if 'api_key' not in st.session_state:
    st.session_state.api_key = None

# Header
st.markdown('<h1 class="main-header">🚀 Agent SEO Multi-Intelligence</h1>', unsafe_allow_html=True)
st.markdown("""
<div style='text-align: center; color: #64748b; margin-bottom: 2rem;'>
    <p style='font-size: 1.2rem;'>Système multi-agents propulsé par l'IA Claude</p>
</div>
""", unsafe_allow_html=True)

# Configuration API dans sidebar
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    api_key = st.text_input(
        "🔑 Clé API Anthropic",
        type="password",
        value=st.session_state.api_key or "",
        help="Obtenez votre clé sur https://console.anthropic.com"
    )
    
    if st.button("💾 Sauvegarder"):
        if api_key:
            st.session_state.api_key = api_key
            st.success("✅ Clé API sauvegardée !")
        else:
            st.error("❌ Veuillez entrer une clé API")
    
    st.markdown("---")
    st.markdown("### 🤖 Agents Disponibles")
    st.markdown("""
    - 🔧 **Analyse Technique**
    - 🔑 **Recherche Mots-Clés**
    - 🎯 **Analyse Concurrence**
    - 📝 **Stratégie Contenu**
    """)

# Fonction d'analyse technique
def analyze_page(url, api_key):
    try:
        # Récupération du contenu
        headers = {'User-Agent': 'Mozilla/5.0 (SEO Agent)'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extraction des données
        title = soup.find('title')
        meta_desc = soup.find('meta', {'name': 'description'})
        h1_tags = soup.find_all('h1')
        h2_tags = soup.find_all('h2')
        images = soup.find_all('img')
        
        data = {
            'url': url,
            'title': title.get_text() if title else None,
            'title_length': len(title.get_text()) if title else 0,
            'meta_desc': meta_desc.get('content') if meta_desc else None,
            'meta_desc_length': len(meta_desc.get('content')) if meta_desc else 0,
            'h1_count': len(h1_tags),
            'h1_tags': [h.get_text().strip() for h in h1_tags],
            'h2_count': len(h2_tags),
            'images_count': len(images),
            'images_without_alt': len([img for img in images if not img.get('alt')])
        }
        
        # Analyse IA avec Claude
        client = anthropic.Anthropic(api_key=api_key)
        
        prompt = f"""Analyse SEO experte de cette page :

URL: {data['url']}
Titre: {data['title']} ({data['title_length']} caractères)
Meta description: {data['meta_desc']} ({data['meta_desc_length']} caractères)
Nombre de H1: {data['h1_count']}
H1 trouvés: {', '.join(data['h1_tags'])}
Nombre de H2: {data['h2_count']}
Images sans alt: {data['images_without_alt']}/{data['images_count']}

Fournis une analyse structurée :
1. Score SEO global /100
2. 3 problèmes critiques
3. 5 recommandations prioritaires
4. Suggestions de mots-clés basées sur le contenu"""

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        return data, message.content[0].text
        
    except Exception as e:
        return None, f"Erreur : {str(e)}"

# Interface principale
tab1, tab2, tab3 = st.tabs(["🔍 Audit Complet", "🔑 Mots-Clés", "📝 Stratégie"])

with tab1:
    st.markdown("## 🔍 Audit SEO Complet")
    
    url_input = st.text_input(
        "🌐 URL à analyser",
        placeholder="https://example.com"
    )
    
    if st.button("🚀 LANCER L'AUDIT", type="primary"):
        if not st.session_state.api_key:
            st.error("❌ Veuillez configurer votre clé API dans la barre latérale")
        elif not url_input:
            st.error("❌ Veuillez entrer une URL")
        else:
            with st.spinner("🤖 Analyse en cours..."):
                data, analysis = analyze_page(url_input, st.session_state.api_key)
                
                if data:
                    st.success("✅ Audit terminé !")
                    
                    # Métriques
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Titre", f"{data['title_length']} car.")
                    with col2:
                        st.metric("Meta Desc", f"{data['meta_desc_length']} car.")
                    with col3:
                        st.metric("H1", data['h1_count'])
                    with col4:
                        st.metric("Images sans alt", data['images_without_alt'])
                    
                    # Analyse IA
                    st.markdown("### 🤖 Analyse IA")
                    st.markdown(analysis)
                    
                    # Export
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            "📥 Télécharger Rapport",
                            data=json.dumps({"data": data, "analysis": analysis}, indent=2),
                            file_name=f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                else:
                    st.error(analysis)

with tab2:
    st.markdown("## 🔑 Recherche de Mots-Clés")
    
    keyword = st.text_input("Mot-clé ou thématique", placeholder="marketing digital")
    
    if st.button("🔎 Rechercher", key="kw_search"):
        if not st.session_state.api_key:
            st.error("❌ Configurez votre clé API d'abord")
        elif keyword:
            with st.spinner("Recherche en cours..."):
                client = anthropic.Anthropic(api_key=st.session_state.api_key)
                
                prompt = f"""Expert SEO : Analyse complète du mot-clé "{keyword}"

Fournis :
1. Évaluation du potentiel (volume estimé, difficulté)
2. 10 mots-clés secondaires
3. 10 mots-clés longue traîne
4. Intention de recherche
5. Stratégie de contenu recommandée"""

                message = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=2000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("### 📊 Résultats")
                st.markdown(message.content[0].text)

with tab3:
    st.markdown("## 📝 Générateur de Stratégie de Contenu")
    
    topic = st.text_input("Sujet du contenu", placeholder="guide marketing digital")
    content_type = st.selectbox("Type", ["Article", "Guide", "Landing page"])
    
    if st.button("✨ Générer Stratégie"):
        if not st.session_state.api_key:
            st.error("❌ Configurez votre clé API d'abord")
        elif topic:
            with st.spinner("Génération..."):
                client = anthropic.Anthropic(api_key=st.session_state.api_key)
                
                prompt = f"""Crée un brief de contenu complet pour : {topic}
Type : {content_type}

Inclus :
1. Titre optimisé SEO
2. Meta description
3. Structure H2/H3 (10-12 sections)
4. Mots-clés à intégrer
5. Longueur recommandée
6. Points clés à couvrir"""

                message = client.messages.create(
                    model="claude-sonnet-4-5-20250929",
                    max_tokens=3000,
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("### 📋 Brief de Contenu")
                st.markdown(message.content[0].text)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1rem 0;'>
    <p><strong>Agent SEO Pro</strong> v1.0 | Propulsé par Claude Sonnet 4.5</p>
</div>
""", unsafe_allow_html=True)
