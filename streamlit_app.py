import streamlit as st
import sys
sys.path.insert(0, '/mount/src/alkosto-ai-assistant/src')

from agent import ConversationEngine, ProductEvaluator
from algolia_client import get_client

st.set_page_config(page_title="Alkosto AI", page_icon="🤖", layout="centered")

# Initialize
if "engine" not in st.session_state:
    st.session_state.engine = ConversationEngine()
    st.session_state.client = get_client()
    st.session_state.stage = "welcome"

st.title("🤖 Alkosto AI Assistant")

# Welcome
if st.session_state.stage == "welcome":
    st.write("👋 ¡Hola! Soy tu asesor experto en computadores.")
    st.write("Te ayudaré a encontrar la laptop perfecta. Contéstame algunas preguntas...")
    
    welcome_msg = st.session_state.engine.get_welcome_message()
    st.info(welcome_msg)
    
    if st.button("Empezar"):
        st.session_state.stage = "chat"
        st.rerun()

# Chat
if st.session_state.stage == "chat":
    # Show history
    for msg in st.session_state.engine.context.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
    
    # Check if ready to search
    if st.session_state.engine.context.profile.is_ready_for_search(0.8):
        if not st.session_state.engine.context.search_results:
            st.info("🔍 Buscando productos...")
            
            # Build filters
            profile = st.session_state.engine.context.profile
            filters = [f"price_sale <= {profile.budget.max}", "in_stock:true"] if profile.budget.max else ["in_stock:true"]
            
            if profile.must_haves.max_weight_kg:
                filters.append(f"weight_kg <= {profile.must_haves.max_weight_kg}")
            if profile.must_haves.min_battery_hours:
                filters.append(f"battery_hours >= {profile.must_haves.min_battery_hours}")
            
            # Search
            result = st.session_state.client.search_products({
                "query": profile.use_case or "laptop",
                "filters": " AND ".join(filters),
                "hits_per_page": 10
            })
            
            st.session_state.engine.set_search_results(result["hits"])
            
            # Evaluate and get top 2
            evaluator = ProductEvaluator(profile)
            scored = evaluator.evaluate(result["hits"], 2)
            
            recommendations = []
            for i, s in enumerate(scored, 1):
                rec = evaluator.format_recommendation(s, i)
                recommendations.append(rec)
            
            st.session_state.engine.set_recommendations(recommendations)
            st.rerun()
    
    # Show recommendations
    if st.session_state.engine.context.recommendations:
        st.success("🎉 Aquí están mis recomendaciones:")
        
        for rec in st.session_state.engine.context.recommendations:
            with st.container():
                cols = st.columns([3, 1])
                with cols[0]:
                    st.subheader(f"{'🏆' if rec['rank'] == 1 else '🥈'} {rec['name']}")
                    st.write(f"**{rec['price_formatted']}** | Match: {rec['match_percentage']}%")
                    st.write(rec['explanation'])
                    st.write(f"💾 {rec['specs']['ram']} | ⚖️ {rec['specs']['weight']} | 🔋 {rec['specs']['battery']}")
                with cols[1]:
                    if st.button(f"Ver detalles", key=f"btn_{rec['object_id']}"):
                        st.markdown(f"[Abrir en Alkosto]({rec['url']})")
                st.divider()
    
    # Chat input
    user_msg = st.chat_input("Tu respuesta...")
    if user_msg:
        result = st.session_state.engine.process_user_message(user_msg)
        
        # Check if search triggered
        if result.get("ready_to_search") and not st.session_state.engine.context.search_results:
            st.rerun()
        else:
            st.rerun()
    
    # Reset button
    if st.button("🔄 Nueva conversación"):
        st.session_state.engine = ConversationEngine()
        st.session_state.engine.context.search_results = []
        st.session_state.engine.context.recommendations = []
        st.rerun()

st.caption("Alkosto AI v1.0 | Powered by Gemini + Algolia")
