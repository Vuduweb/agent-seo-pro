import streamlit as st
import anthropic
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
from urllib.parse import urlparse
import time
import re

# ============================================
# CONFIGURATION STREAMLIT
# ============================================

st.set_page_config(
    page_title="SEO Intelligence Suite Pro v5.0",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CSS PERSONNALISÉ
# ============================================

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

    .metric-card-pro {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 5px solid #3b82f6;
        transition: all 0.3s ease;
    }

    .metric-card-pro:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }

    .chat-message {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #3b82f6;
    }

    .chat-message.user {
        background: #eff6ff;
        border-left-color: #2563eb;
    }

    .chat-message.assistant {
        background: #f0fdf4;
        border-left-color: #10b981;
    }

    .tag { 
        display: inline-block; 
        padding: 0.3rem 0.8rem; 
        border-radius: 20px; 
        font-size: 0.75rem; 
        font-weight: 600; 
        margin: 0.2rem;
    }

    .tag-p0 { background: #fee2e2; color: #991b1b; }
    .tag-p1 { background: #fef3c7; color: #92400e; }
    .tag-p2 { background: #dbeafe; color: #1e40af; }
    .tag-high { background: #fecaca; color: #991b1b; }
    .tag-medium { background: #fde68a; color: #92400e; }
    .tag-low { background: #bfdbfe; color: #1e40af; }

    .roi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(102,126,234,0.3);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# SESSION STATE INITIALIZATION
# ============================================

if 'anthropic_key' not in st.session_state:
    st.session_state.anthropic_key = None

if 'paa_questions' not in st.session_state:
    st.session_state.paa_questions = []

if 'paa_selected' not in st.session_state:
    st.session_state.paa_selected = []

if 'paa_content_generated' not in st.session_state:
    st.session_state.paa_content_generated = []

if 'linking_suggestions' not in st.session_state:
    st.session_state.linking_suggestions = {}

if 'paa_keyword' not in st.session_state:
    st.session_state.paa_keyword = ""

if 'paa_brand_context' not in st.session_state:
    st.session_state.paa_brand_context = ""

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'links_injected' not in st.session_state:
    st.session_state.links_injected = False

if 'roi_data' not in st.session_state:
    st.session_state.roi_data = {
        'cost_per_article': 15.0,
        'time_per_article': 3.0,
        'hourly_rate': 50.0
    }# ============================================
    # FONCTIONS PRINCIPALES
    # ============================================

    def extract_paa_questions(keyword, anthropic_key, num=20):
        """Extrait les questions PAA avec Claude"""
        client = anthropic.Anthropic(api_key=anthropic_key)

        prompt = f"""Tu es un expert SEO. Génère {num} questions PAA (People Also Ask) réalistes et variées pour le mot-clé "{keyword}".

    Format JSON strict requis:
    {{
      "paa_questions": [
        {{
          "question": "Question PAA complète et naturelle ?",
          "priority": "P0",
          "difficulty": "easy",
          "search_intent": "informational",
          "estimated_volume": "high",
          "related_keywords": ["kw1", "kw2", "kw3"],
          "content_type": "Article",
          "content_angle": "Comment faire X",
          "target_length": "1500-2000 words"
        }}
      ]
    }}

    Critères:
    - Questions variées (comment, pourquoi, quoi, combien, etc.)
    - Priorité: P0 (haute), P1 (moyenne), P2 (basse)
    - Difficulté: easy, medium, hard
    - Intent: informational, transactional, navigational
    - Volume: high, medium, low

    Réponds UNIQUEMENT avec le JSON, rien d'autre."""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )

            text = message.content[0].text
            json_match = re.search(r'\{[\s\S]*\}', text)

            if json_match:
                data = json.loads(json_match.group(0))
                return data

            return {"paa_questions": []}

        except Exception as e:
            st.error(f"Erreur extraction PAA: {str(e)}")
            return {"paa_questions": []}


    def generate_paa_content(question_data, anthropic_key, brand_context=""):
        """Génère un article SEO complet optimisé"""
        client = anthropic.Anthropic(api_key=anthropic_key)

        related_kw = ', '.join(question_data.get('related_keywords', [])[:5])
        brand_text = f"CONTEXTE MARQUE: {brand_context}" if brand_context else ""

        prompt = f"""Rédige un article SEO COMPLET, PROFESSIONNEL et OPTIMISÉ pour:

    QUESTION: {question_data['question']}
    TYPE: {question_data.get('content_type', 'Article')}
    LONGUEUR: {question_data.get('target_length', '1500-2000 mots')}
    MOTS-CLÉS: {related_kw}

    {brand_text}

    STRUCTURE OBLIGATOIRE:

    # [Titre H1 optimisé avec la question principale]

    **Meta Description (150-160 caractères):**
    [Meta description accrocheuse et optimisée SEO]

    ---

    ## Introduction (100-150 mots)
    [Intro engageante qui reformule la question, présente le problème et annonce la structure du contenu]

    ---

    ## Réponse Directe - En Bref
    [Paragraphe de 50-75 mots répondant directement à la question. Format optimisé pour featured snippet]

    **Points clés:**
    - Point essentiel 1
    - Point essentiel 2  
    - Point essentiel 3

    ---

    ## [H2: Premier aspect principal]
    ### [H3: Sous-section détaillée 1.1]
    [Contenu détaillé et approfondi de 200-300 mots avec exemples concrets]

    ### [H3: Sous-section détaillée 1.2]
    [Contenu détaillé et approfondi de 200-300 mots avec exemples concrets]

    ---

    ## [H2: Deuxième aspect principal]
    [Développement complet de 400-500 mots avec données, statistiques, conseils pratiques]

    ---

    ## [H2: Troisième aspect principal]  
    [Cas pratiques, exemples réels, études de cas - 400-500 mots]

    ---

    ## [H2: Conseils Pratiques]
    [Section actionnable avec conseils concrets]

    ### [H3: Ce qu'il faut faire]
    - Conseil 1 avec explication
    - Conseil 2 avec explication
    - Conseil 3 avec explication

    ### [H3: Ce qu'il faut éviter]
    - Erreur 1 à éviter
    - Erreur 2 à éviter
    - Erreur 3 à éviter

    ---

    ## Questions Fréquentes (FAQ)

    ### Question 1 pertinente ?
    [Réponse courte et précise de 50-75 mots]

    ### Question 2 pertinente ?
    [Réponse courte et précise de 50-75 mots]

    ### Question 3 pertinente ?
    [Réponse courte et précise de 50-75 mots]

    ### Question 4 pertinente ?
    [Réponse courte et précise de 50-75 mots]

    ### Question 5 pertinente ?
    [Réponse courte et précise de 50-75 mots]

    ### Question 6 pertinente ?
    [Réponse courte et précise de 50-75 mots]

    ---

    ## Points Clés à Retenir
    - Point synthétique 1
    - Point synthétique 2
    - Point synthétique 3
    - Point synthétique 4
    - Point synthétique 5

    ---

    ## Conclusion
    [Résumé en 100-150 mots + appel à l'action naturel et subtil]

    ---

    **MÉTADONNÉES SEO:**
    - **Mots-clés principaux:** [liste de 3-5 mots-clés]
    - **Mots-clés secondaires:** [liste de 10-15 mots-clés LSI]
    - **Liens internes suggérés:** [3-5 ancres de liens avec contexte]
    - **Images recommandées:** [3-5 descriptions d'images à créer]

    ---

    EXIGENCES:
    - Contenu 100% original et unique
    - Ton professionnel mais accessible
    - Paragraphes courts (3-4 lignes max)
    - Optimisé pour LLM et AI Overview
    - Riche en informations concrètes
    - Exemples et données chiffrées
    - Aucun fluff, que du contenu utile"""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=16000,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text

        except Exception as e:
            return f"Erreur lors de la génération: {str(e)}"


    def generate_visual_guide(article_content, question, anthropic_key):
        """Génère un guide visuel complet avec prompts IA"""
        client = anthropic.Anthropic(api_key=anthropic_key)

        content_sample = article_content[:1000]

        prompt = f"""Crée un GUIDE VISUEL COMPLET et DÉTAILLÉ pour illustrer cet article:

    QUESTION: {question}
    CONTENU (extrait): {content_sample}

    Format JSON requis:
    {{
      "hero_image": {{
        "description": "Description détaillée de l'image principale",
        "dalle_prompt": "Prompt ultra-détaillé pour DALL-E 3",
        "midjourney_prompt": "Prompt optimisé pour Midjourney v6",
        "dimensions": "1200x630px",
        "alt_text": "ALT text SEO-optimized descriptif"
      }},
      "infographic": {{
        "title": "Titre accrocheur de l'infographie",
        "description": "Description complète",
        "dalle_prompt": "Prompt DALL-E pour infographie",
        "dimensions": "800x2000px",
        "sections": ["Section 1", "Section 2", "Section 3"]
      }},
      "section_images": [
        {{
          "section": "Nom de la section H2",
          "description": "Description de l'image",
          "dalle_prompt": "Prompt détaillé et optimisé",
          "alt_text": "ALT text descriptif",
          "dimensions": "800x500px",
          "image_type": "illustration"
        }}
      ],
      "pinterest_pins": [
        {{
          "title": "Titre du pin vertical",
          "dalle_prompt": "Prompt pour format vertical Pinterest",
          "text_overlay": "Texte à superposer",
          "dimensions": "1000x1500px"
        }}
      ]
    }}

    Réponds UNIQUEMENT avec le JSON."""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=6000,
                messages=[{"role": "user", "content": prompt}]
            )

            text = message.content[0].text
            json_match = re.search(r'\{[\s\S]*\}', text)

            if json_match:
                return json.loads(json_match.group(0))

            return {}

        except Exception as e:
            st.error(f"Erreur génération visuels: {str(e)}")
            return {}


    def generate_internal_linking(articles_data, anthropic_key):
        """Génère une stratégie de maillage interne intelligente"""
        client = anthropic.Anthropic(api_key=anthropic_key)

        articles_summary = []
        for idx, article in enumerate(articles_data[:20]):
            articles_summary.append({
                'id': idx,
                'question': article['question'],
                'sample': article['content'][:300],
                'priority': article['metadata'].get('priority', 'P2')
            })

        articles_json = json.dumps(articles_summary, ensure_ascii=False)[:4000]

        prompt = f"""Crée une STRATÉGIE DE MAILLAGE INTERNE INTELLIGENTE pour {len(articles_summary)} articles:

    {articles_json}

    Format JSON requis:
    {{
      "silo_structure": [
        {{
          "silo_name": "Nom du silo thématique",
          "pillar_page": {{
            "id": 0,
            "title": "Titre de la page pilier",
            "why_pillar": "Raison"
          }},
          "cluster_pages": [1, 2, 3, 4]
        }}
      ],
      "linking_matrix": [
        {{
          "from_id": 0,
          "from_title": "Titre article source",
          "links": [
            {{
              "to_id": 1,
              "to_title": "Titre article cible",
              "anchor_text": "Ancre naturelle",
              "anchor_variations": ["Var 1", "Var 2"],
              "context": "Phrase avec [ANCHOR]",
              "placement": "Introduction",
              "seo_value": "high",
              "reasoning": "Raison"
            }}
          ]
        }}
      ],
      "metrics": {{
        "total_links": 0,
        "avg_links_per_page": 0,
        "silos_count": 0
      }},
      "recommendations": ["Recommandation 1", "Recommandation 2"]
    }}

    Réponds UNIQUEMENT avec le JSON."""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=12000,
                messages=[{"role": "user", "content": prompt}]
            )

            text = message.content[0].text
            json_match = re.search(r'\{[\s\S]*\}', text)

            if json_match:
                return json.loads(json_match.group(0))

            return {}

        except Exception as e:
            st.error(f"Erreur génération maillage: {str(e)}")
            return {}


    def inject_internal_links(articles, linking_matrix):
        """Injecte automatiquement les liens dans les articles"""

        injected_articles = []
        injection_stats = {
            'total_injections': 0,
            'articles_modified': 0,
            'links_per_article': {}
        }

        for article_idx, article in enumerate(articles):
            modified_content = article['content']
            links_injected = 0

            article_links = []
            for link_group in linking_matrix:
                if link_group.get('from_id') == article_idx:
                    article_links = link_group.get('links', [])
                    break

            for link in article_links:
                anchor = link.get('anchor_text', '')
                context = link.get('context', '')
                to_id = link.get('to_id')

                if anchor and context:
                    link_markdown = f"[{anchor}](#article-{to_id})"

                    if '[ANCHOR]' in context:
                        injected_context = context.replace('[ANCHOR]', link_markdown)
                    else:
                        injected_context = context.replace(anchor, link_markdown)

                    placement = link.get('placement', 'Introduction')

                    if 'introduction' in placement.lower():
                        intro_end = modified_content.find('\n---\n', 200)
                        if intro_end > 0:
                            modified_content = (
                                modified_content[:intro_end] +
                                f"\n\n{injected_context}\n" +
                                modified_content[intro_end:]
                            )
                            links_injected += 1
                    else:
                        conclusion_start = modified_content.rfind('## Conclusion')
                        if conclusion_start > 0:
                            modified_content = (
                                modified_content[:conclusion_start] +
                                f"\n\n{injected_context}\n\n" +
                                modified_content[conclusion_start:]
                            )
                            links_injected += 1

            if links_injected > 0:
                injection_stats['articles_modified'] += 1
                injection_stats['total_injections'] += links_injected
                injection_stats['links_per_article'][article_idx] = links_injected

            injected_articles.append({
                **article,
                'content': modified_content,
                'links_injected': links_injected
            })

        return injected_articles, injection_stats


    def calculate_roi(articles_data, roi_params):
        """Calcule le ROI détaillé de la production de contenu"""

        num_articles = len(articles_data)
        total_words = sum([len(a['content'].split()) for a in articles_data])

        cost_per_article = roi_params.get('cost_per_article', 15.0)
        total_cost = num_articles * cost_per_article

        time_per_article_manual = roi_params.get('time_per_article', 3.0)
        time_per_article_auto = 0.5

        time_saved_hours = num_articles * (time_per_article_manual - time_per_article_auto)

        hourly_rate = roi_params.get('hourly_rate', 50.0)
        value_time_saved = time_saved_hours * hourly_rate

        roi_percentage = ((value_time_saved - total_cost) / total_cost * 100) if total_cost > 0 else 0

        avg_words_per_article = total_words // num_articles if num_articles > 0 else 0
        cost_per_word = total_cost / total_words if total_words > 0 else 0

        estimated_traffic_per_article = 500
        estimated_conversion_rate = 0.02
        estimated_value_per_conversion = 100

        monthly_value = (
            num_articles * 
            estimated_traffic_per_article * 
            estimated_conversion_rate * 
            estimated_value_per_conversion
        )

        annual_value = monthly_value * 12

        return {
            'num_articles': num_articles,
            'total_words': total_words,
            'avg_words_per_article': avg_words_per_article,
            'total_cost': total_cost,
            'cost_per_article': cost_per_article,
            'cost_per_word': cost_per_word,
            'time_saved_hours': time_saved_hours,
            'value_time_saved': value_time_saved,
            'roi_percentage': roi_percentage,
            'monthly_value_estimate': monthly_value,
            'annual_value_estimate': annual_value,
            'break_even_months': (total_cost / monthly_value) if monthly_value > 0 else 0
        }


    def generate_client_report(articles_data, linking_data, roi_data, anthropic_key):
        """Génère un rapport client professionnel"""
        client = anthropic.Anthropic(api_key=anthropic_key)

        summary = {
            'total_articles': len(articles_data),
            'total_words': sum([len(a['content'].split()) for a in articles_data]),
            'articles_with_visuals': len([a for a in articles_data if a.get('visuals')]),
            'total_links': linking_data.get('metrics', {}).get('total_links', 0),
            'silos_count': linking_data.get('metrics', {}).get('silos_count', 0)
        }

        prompt = f"""Crée un RAPPORT CLIENT PROFESSIONNEL pour une livraison de contenu SEO:

    DONNÉES DU PROJET:
    - Articles générés: {summary['total_articles']}
    - Mots totaux: {summary['total_words']}
    - Articles avec visuels: {summary['articles_with_visuals']}
    - Liens internes: {summary['total_links']}
    - Silos thématiques: {summary['silos_count']}

    ROI:
    - Investissement total: {roi_data.get('total_cost', 0):.2f} euros
    - Temps économisé: {roi_data.get('time_saved_hours', 0):.1f}h
    - Valeur générée: {roi_data.get('value_time_saved', 0):.2f} euros
    - ROI: {roi_data.get('roi_percentage', 0):.1f}%
    - Valeur estimée annuelle: {roi_data.get('annual_value_estimate', 0):.0f} euros

    Crée un rapport structuré avec:

    # RAPPORT DE PRODUCTION SEO

    ## 1. RÉSUMÉ EXÉCUTIF
    [Synthèse en 3-4 paragraphes]

    ## 2. LIVRABLES
    ### 2.1 Contenu Produit
    [Détails sur les articles]

    ### 2.2 Visuels et Médias
    [Détails sur les guides visuels]

    ### 2.3 Maillage Interne
    [Stratégie de liens]

    ## 3. MÉTRIQUES ET PERFORMANCE
    ### 3.1 Métriques de Production
    [Tableaux de chiffres]

    ### 3.2 ROI et Valeur
    [Analyse financière]

    ## 4. RECOMMANDATIONS
    ### 4.1 Prochaines Étapes
    [5-7 recommandations actionnables]

    ### 4.2 Optimisations Futures
    [Suggestions d'amélioration]

    ## 5. PLAN D'ACTION
    [Timeline et tâches concrètes]

    Format: Markdown professionnel avec mise en forme."""

        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}]
            )

            return message.content[0].text

        except Exception as e:
            return f"Erreur génération rapport: {str(e)}"


    def generate_dev_tickets(linking_data, articles_data):
        """Génère des tickets de développement"""
        tickets = []
        total_links = linking_data.get('metrics', {}).get('total_links', 0)

        ticket_links = f"""# TICKET DEV #001 - Injection Liens Internes

    ## Priorité: HAUTE
    ## Temps estimé: 4-6h

    ## Description
    Implémenter les {total_links} liens internes dans les {len(articles_data)} articles.

    ## Acceptance Criteria
    - [ ] Tous les liens insérés
    - [ ] Ancres naturelles
    - [ ] Tests effectués
    """
        tickets.append(ticket_links)
        return tickets


    def chat_with_assistant(user_message, articles_data, linking_data, anthropic_key):
        """Assistant IA conversationnel"""
        client = anthropic.Anthropic(api_key=anthropic_key)

        total_words = sum([len(a['content'].split()) for a in articles_data])

        context = f"""Tu es un assistant SEO expert.

    PROJET:
    - {len(articles_data)} articles générés
    - {total_words} mots au total

    Réponds de manière claire et actionnable."""

        messages = [{"role": "user", "content": context}]

        for msg in st.session_state.chat_history[-6:]:
            messages.append(msg)

        messages.append({"role": "user", "content": user_message})

        try:
            message = client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                messages=messages
            )

            return message.content[0].text

        except Exception as e:
            return f"Erreur: {str(e)}"
            # ============================================
            # HEADER
            # ============================================

            st.markdown('<h1 class="main-header">SEO Intelligence Suite Pro</h1>', unsafe_allow_html=True)
            st.markdown("""
            <p style="text-align: center; color: #64748b; font-size: 1.2rem; margin-bottom: 2rem;">
                <strong>Version 5.0 COMPLÈTE</strong> - Production • Visuels • Maillage • ROI • Rapports • Assistant IA
            </p>
            """, unsafe_allow_html=True)

            # ============================================
            # SIDEBAR
            # ============================================

            with st.sidebar:
                st.markdown("## Configuration")

                anthropic_key = st.text_input(
                    "Clé API Anthropic",
                    type="password",
                    value=st.session_state.anthropic_key or "",
                    help="Obtenez votre clé sur https://console.anthropic.com"
                )

                if st.button("Sauvegarder Configuration", type="primary", use_container_width=True):
                    if anthropic_key:
                        st.session_state.anthropic_key = anthropic_key
                        st.success("Configuration sauvegardée !")
                    else:
                        st.error("Clé Anthropic requise")

                st.markdown("---")
                st.markdown("### Statistiques Session")

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Articles", len(st.session_state.paa_content_generated))
                    st.metric("Questions", len(st.session_state.paa_questions))

                with col2:
                    if st.session_state.paa_content_generated:
                        total_words = sum([len(a['content'].split()) for a in st.session_state.paa_content_generated])
                        st.metric("Mots", f"{total_words:,}")

                        articles_with_visuals = len([a for a in st.session_state.paa_content_generated if a.get('visuals')])
                        st.metric("Visuels", articles_with_visuals)

            # Interface principale
            tabs = st.tabs([
                "PAA Factory",
                "Injection Liens", 
                "ROI & Analytics",
                "Rapports & Tickets",
                "Assistant IA",
                "Paramètres"
            ])

            # TAB 1: PAA FACTORY
            with tabs[0]:
                st.markdown("## PAA Content Factory")

                st.markdown("### ÉTAPE 1: Extraction des Questions PAA")

                col1, col2 = st.columns([3, 1])

                with col1:
                    paa_keyword = st.text_input(
                        "Mot-clé principal",
                        placeholder="Ex: marketing digital"
                    )

                with col2:
                    num_paa = st.number_input("Nombre", 5, 50, 20, 5)

                brand_context = st.text_area("Contexte marque (optionnel)", height=80)

                if st.button("EXTRAIRE LES QUESTIONS PAA", type="primary", use_container_width=True):
                    if not st.session_state.anthropic_key:
                        st.error("Configurez votre clé API")
                    elif not paa_keyword:
                        st.error("Entrez un mot-clé")
                    else:
                        with st.spinner("Extraction en cours..."):
                            paa_data = extract_paa_questions(paa_keyword, st.session_state.anthropic_key, num_paa)
                            st.session_state.paa_questions = paa_data.get('paa_questions', [])
                            st.session_state.paa_keyword = paa_keyword
                            st.session_state.paa_brand_context = brand_context

                            if st.session_state.paa_questions:
                                st.success(f"{len(st.session_state.paa_questions)} questions extraites !")
                                time.sleep(0.5)
                                st.rerun()

                if st.session_state.paa_questions:
                    st.markdown("---")
                    st.markdown("### ÉTAPE 2: Sélection")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        if st.button("Tout sélectionner", use_container_width=True):
                            st.session_state.paa_selected = list(range(len(st.session_state.paa_questions)))
                            st.rerun()
                    with col2:
                        if st.button("Désélectionner", use_container_width=True):
                            st.session_state.paa_selected = []
                            st.rerun()
                    with col3:
                        if st.button("P0 seulement", use_container_width=True):
                            st.session_state.paa_selected = [i for i, q in enumerate(st.session_state.paa_questions) if q.get('priority') == 'P0']
                            st.rerun()
                    with col4:
                        if st.button("P0 + P1", use_container_width=True):
                            st.session_state.paa_selected = [i for i, q in enumerate(st.session_state.paa_questions) if q.get('priority') in ['P0', 'P1']]
                            st.rerun()

                    for idx, q in enumerate(st.session_state.paa_questions):
                        priority = q.get('priority', 'P2')
                        is_selected = idx in st.session_state.paa_selected

                        if st.checkbox(f"{q['question']}", value=is_selected, key=f"sel_{idx}"):
                            if idx not in st.session_state.paa_selected:
                                st.session_state.paa_selected.append(idx)
                        else:
                            if idx in st.session_state.paa_selected:
                                st.session_state.paa_selected.remove(idx)

                    if st.session_state.paa_selected:
                        st.markdown("---")
                        st.success(f"{len(st.session_state.paa_selected)} question(s) sélectionnée(s)")

                        if st.button(f"GÉNÉRER {len(st.session_state.paa_selected)} ARTICLES", type="primary", use_container_width=True):
                            progress_bar = st.progress(0)

                            for i, idx in enumerate(st.session_state.paa_selected):
                                question_data = st.session_state.paa_questions[idx]

                                content = generate_paa_content(
                                    question_data,
                                    st.session_state.anthropic_key,
                                    st.session_state.get('paa_brand_context', '')
                                )

                                st.session_state.paa_content_generated.append({
                                    'question': question_data['question'],
                                    'content': content,
                                    'metadata': question_data,
                                    'timestamp': datetime.now().isoformat(),
                                    'keyword': st.session_state.get('paa_keyword', '')
                                })

                                progress_bar.progress((i + 1) / len(st.session_state.paa_selected))
                                time.sleep(0.5)

                            st.success("Articles générés !")
                            st.session_state.paa_selected = []
                            st.rerun()

                if st.session_state.paa_content_generated:
                    st.markdown("---")
                    st.markdown("### Articles Générés")

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        if st.button("Générer Visuels", use_container_width=True):
                            with st.spinner("Génération visuels..."):
                                for article in st.session_state.paa_content_generated:
                                    if 'visuals' not in article:
                                        visuals = generate_visual_guide(article['content'], article['question'], st.session_state.anthropic_key)
                                        article['visuals'] = visuals
                                st.success("Visuels générés !")
                                st.rerun()

                    with col2:
                        if st.button("Générer Maillage", use_container_width=True):
                            with st.spinner("Génération maillage..."):
                                linking = generate_internal_linking(st.session_state.paa_content_generated, st.session_state.anthropic_key)
                                st.session_state.linking_suggestions = linking
                                st.success("Maillage généré !")
                                st.rerun()

                    with col3:
                        date_str = datetime.now().strftime('%Y%m%d')
                        all_content = "\n\n".join([f"# ARTICLE {i+1}\n\n{a['content']}" for i, a in enumerate(st.session_state.paa_content_generated)])
                        st.download_button("Télécharger TOUT", data=all_content, file_name=f"articles_{date_str}.md", mime="text/markdown", use_container_width=True)

                    for idx, article in enumerate(st.session_state.paa_content_generated):
                        with st.expander(f"Article #{idx+1}: {article['question'][:60]}...", expanded=(idx==len(st.session_state.paa_content_generated)-1)):
                            st.markdown(article['content'])
                            st.download_button("Télécharger", data=article['content'], file_name=f"article_{idx+1}.md", mime="text/markdown", key=f"dl_{idx}")

            # TAB 2: INJECTION
            with tabs[1]:
                st.markdown("## Injection Automatique des Liens")

                if not st.session_state.paa_content_generated:
                    st.info("Générez d'abord du contenu")
                elif not st.session_state.linking_suggestions:
                    st.warning("Générez d'abord le maillage interne")
                else:
                    if st.button("INJECTER TOUS LES LIENS", type="primary", use_container_width=True):
                        with st.spinner("Injection..."):
                            linking_matrix = st.session_state.linking_suggestions.get('linking_matrix', [])
                            injected_articles, stats = inject_internal_links(st.session_state.paa_content_generated, linking_matrix)
                            st.session_state.paa_content_generated = injected_articles
                            st.session_state.links_injected = True
                            st.success(f"Injection terminée ! {stats['total_injections']} liens injectés")
                            st.rerun()

            # TAB 3: ROI
            with tabs[2]:
                st.markdown("## ROI & Analytics")

                if st.session_state.paa_content_generated:
                    roi_data = calculate_roi(st.session_state.paa_content_generated, st.session_state.roi_data)

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("ROI", f"{roi_data['roi_percentage']:.1f}%")
                    with col2:
                        st.metric("Valeur Générée", f"{roi_data['value_time_saved']:,.0f}€")
                    with col3:
                        st.metric("Investissement", f"{roi_data['total_cost']:.0f}€")
                    with col4:
                        st.metric("Temps Économisé", f"{roi_data['time_saved_hours']:.1f}h")
                else:
                    st.info("Générez du contenu pour voir le ROI")

            # TAB 4: RAPPORTS
            with tabs[3]:
                st.markdown("## Rapports & Tickets")

                if st.session_state.paa_content_generated:
                    if st.button("GÉNÉRER RAPPORT CLIENT", type="primary"):
                        with st.spinner("Génération rapport..."):
                            roi_data = calculate_roi(st.session_state.paa_content_generated, st.session_state.roi_data)
                            report = generate_client_report(st.session_state.paa_content_generated, st.session_state.linking_suggestions, roi_data, st.session_state.anthropic_key)
                            st.session_state['last_report'] = report
                            st.success("Rapport généré !")

                    if 'last_report' in st.session_state:
                        st.markdown(st.session_state['last_report'])
                        date_str = datetime.now().strftime('%Y%m%d')
                        st.download_button("Télécharger Rapport", data=st.session_state['last_report'], file_name=f"rapport_{date_str}.md", mime="text/markdown")
                else:
                    st.info("Générez du contenu d'abord")

            # TAB 5: ASSISTANT
            with tabs[4]:
                st.markdown("## Assistant IA")

                if st.session_state.paa_content_generated:
                    for msg in st.session_state.chat_history:
                        role = msg['role']
                        content = msg['content']
                        if role == 'user':
                            st.markdown(f"**Vous:** {content}")
                        else:
                            st.markdown(f"**Assistant:** {content}")

                    user_input = st.text_area("Votre message", height=100)

                    if st.button("ENVOYER", type="primary"):
                        if user_input:
                            st.session_state.chat_history.append({'role': 'user', 'content': user_input})
                            response = chat_with_assistant(user_input, st.session_state.paa_content_generated, st.session_state.linking_suggestions, st.session_state.anthropic_key)
                            st.session_state.chat_history.append({'role': 'assistant', 'content': response})
                            st.rerun()
                else:
                    st.info("Générez du contenu d'abord")

            # TAB 6: PARAMÈTRES
            with tabs[5]:
                st.markdown("## Paramètres")

                if st.button("Supprimer Tous les Articles", type="secondary"):
                    if st.checkbox("Confirmer"):
                        st.session_state.paa_content_generated = []
                        st.session_state.linking_suggestions = {}
                        st.session_state.links_injected = False
                        st.success("Articles supprimés")
                        st.rerun()

            # FOOTER
            st.markdown("---")
            st.markdown("""
            <div style='text-align: center; padding: 2rem;'>
                <h3>SEO Intelligence Suite Pro v5.0</h3>
                <p>Production Automatisée de Contenu SEO Premium</p>
            </div>
            """, unsafe_allow_html=True)
            
