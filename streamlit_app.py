import streamlit as st
from algolia_client import get_client, DEMO_PRODUCTS
import time

# Page config
st.set_page_config(
    page_title="Alkosto - Asistente IA",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Initialize
client = get_client()

# CSS - nur für Container, nicht für Widgets
st.markdown("""
<style>
    .main {
        max-width: 800px;
        margin: 0 auto;
    }
    .stTextInput > div > div > input {
        border-radius: 25px;
        padding: 12px 20px;
        border: 2px solid #e5e7eb;
        font-size: 16px;
    }
    .stButton > button {
        border-radius: 25px;
        padding: 12px 24px;
        background-color: #3b82f6;
        color: white;
        border: none;
        font-weight: 500;
    }
    .stButton > button:hover {
        background-color: #2563eb;
    }
</style>
""", unsafe_allow_html=True)

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.stage = "welcome"
    st.session_state.context = {
        "use_case": None,
        "budget": None,
        "priorities": []
    }

def process_message(message):
    """Process user message and generate response"""
    st.session_state.messages.append({"role": "user", "content": message})
    
    # Parse intent from message
    msg_lower = message.lower()
    
    # Extract use case
    if "estudio" in msg_lower or "estudiante" in msg_lower:
        st.session_state.context["use_case"] = "estudio"
    elif "gaming" in msg_lower or "juego" in msg_lower:
        st.session_state.context["use_case"] = "gaming"
    elif "oficina" in msg_lower or "trabajo" in msg_lower:
        st.session_state.context["use_case"] = "oficina"
    elif "ligero" in msg_lower or "viaje" in msg_lower or "portatil" in msg_lower:
        st.session_state.context["use_case"] = "portatil"
    elif "bateria" in msg_lower:
        st.session_state.context["use_case"] = "bateria"
    
    # Build filters
    filters = ["in_stock:true"]
    
    # Default budget if not set
    if st.session_state.context["budget"] is None:
        st.session_state.context["budget"] = 3000000
    
    filters.append(f"price_sale < {st.session_state.context['budget']}")
    
    # Use case specific filters
    if st.session_state.context["use_case"] == "portatil":
        filters.append("weight_kg < 1.5")
    elif st.session_state.context["use_case"] == "bateria":
        filters.append("battery_hours > 10")
    
    # Search
    try:
        result = client.search_products({
            "query": st.session_state.context.get("use_case", "laptop"),
            "filters": " AND ".join(filters),
            "hits_per_page": 3
        })
        
        if result["hits"]:
            # Generate bot response
            best = result["hits"][0]
            response = f"💡 Encontré **{result['total']} laptops** que pueden interesarte."
            response += f"\n\n🏆 **Mi recomendación:** {best['name']}"
            response += f"\n\n**Por qué es ideal para ti:**"
            response += f"\n• Excelente relación precio/rendimiento"
            response += f"\n• {best.get('ram', '8GB')} de RAM"
            if best.get('weight_kg'):
                response += f"\n• Solo {best['weight_kg']} kg"
            if best.get('battery_hours'):
                response += f"\n• Hasta {best['battery_hours']} horas de batería"
            
            response += f"\n\n💵 **Precio:** ${best['price_sale']:,} COP"
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })
            
            # Add product cards if multiple results
            if len(result["hits"]) > 1:
                st.session_state.messages.append({
                    "role": "assistant",
                    "type": "products",
                    "products": result["hits"][:2]
                })
        else:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "😕 No encontré laptops con esos criterios exactos. ¿Puedes darme más detalles sobre tu presupuesto o prioridades?"
            })
            
    except Exception as e:
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ Lo siento, tuve un problema buscando."
        })

# Welcome Screen
if st.session_state.stage == "welcome":
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; font-size: 2.5rem;'>👋 Hola, soy tu asesor experto en computadores</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 1.2rem; color: #6b7280;'>Encuentra tu portátil ideal sin tecnicismos. Cuéntame lo que buscas.</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Suggestion buttons
    st.markdown("<p style='text-align: center; color: #9ca3af;'>Sugerencias:</p>", unsafe_allow_html=True)
    
    suggestions_row1 = st.columns(3)
    with suggestions_row1[0]:
        if st.button("💻 Laptop para estudio", use_container_width=True):
            process_message("Laptop para estudio")
            st.session_state.stage = "chat"
            st.rerun()
    with suggestions_row1[1]:
        if st.button("🎮 Gaming", use_container_width=True):
            process_message("Laptop para gaming")
            st.session_state.stage = "chat"
            st.rerun()
    with suggestions_row1[2]:
        if st.button("💼 Oficina", use_container_width=True):
            process_message("Laptop para oficina")
            st.session_state.stage = "chat"
            st.rerun()
    
    suggestions_row2 = st.columns(3)
    with suggestions_row2[0]:
        if st.button("✈️ Ligero para viajar", use_container_width=True):
            process_message("Laptop ligera para viajar")
            st.session_state.stage = "chat"
            st.rerun()
    with suggestions_row2[1]:
        if st.button("🔋 Buena batería", use_container_width=True):
            process_message("Laptop con buena batería")
            st.session_state.stage = "chat"
            st.rerun()
    with suggestions_row2[2]:
        if st.button("💰 Menos de 2M COP", use_container_width=True):
            process_message("Laptop barata menos de 2 millones")
            st.session_state.stage = "chat"
            st.rerun()
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Free input
    user_input = st.text_input("O escribe tu búsqueda...", key="welcome_input", placeholder="Ej: Necesito laptop para universidad, ligera y barata")
    if st.button("Buscar 🔍", type="primary", use_container_width=True):
        if user_input:
            process_message(user_input)
            st.session_state.stage = "chat"
            st.rerun()

# Chat Interface
if st.session_state.stage == "chat":
    # Display messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            if msg.get("type") == "products":
                st.markdown("---")
                st.markdown("**También te pueden interesar:**")
                for product in msg["products"]:
                    with st.container():
                        st.markdown(f"**{product['name']}**")
                        st.markdown(f"💵 ${product['price_sale']:,} COP | 💾 {product.get('ram', 'N/A')} | ⚖️ {product.get('weight_kg', 'N/A')} kg")
                        if st.button(f"Ver detalles ↗", key=f"link_{product['objectID']}"):
                            st.markdown(f"[Abrir en Alkosto]({product['url']})")
                        st.markdown("---")
            else:
                with st.chat_message("assistant"):
                    st.markdown(msg["content"])
    
    # Quick replies after last message
    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "assistant":
        st.markdown("<p style='color: #9ca3af; font-size: 0.9rem;'>Sugerencias:</p>", unsafe_allow_html=True)
        cols = st.columns(4)
        quick_replies = ["Más barato", "Más ligero", "Más potente", "Ver alternativas"]
        for i, reply in enumerate(quick_replies):
            with cols[i]:
                if st.button(reply, key=f"quick_{i}_{len(st.session_state.messages)}", use_container_width=True):
                    process_message(reply)
                    st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Chat input at bottom
    user_msg = st.chat_input("Escribe tu mensaje...")
    if user_msg:
        process_message(user_msg)
        st.rerun()
    
    # Back to welcome button
    if st.button("← Nueva búsqueda", type="secondary"):
        st.session_state.messages = []
        st.session_state.stage = "welcome"
        st.rerun()

# Footer
st.markdown("---")
st.caption("Alkosto AI Assistant v0.3 | Powered by Algolia + Streamlit")
