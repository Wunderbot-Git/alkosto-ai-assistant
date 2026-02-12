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

# CSS for Chat-Interface
st.markdown("""
<style>
    .main {
        max-width: 800px;
        margin: 0 auto;
    }
    .chat-container {
        max-width: 700px;
        margin: 0 auto;
    }
    .welcome-title {
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .welcome-subtitle {
        font-size: 1.2rem;
        text-align: center;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .suggestion-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        justify-content: center;
        margin: 1rem 0;
    }
    .suggestion-pill {
        background-color: #f3f4f6;
        color: #374151;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: 1px solid #e5e7eb;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.2s;
    }
    .suggestion-pill:hover {
        background-color: #e5e7eb;
        border-color: #d1d5db;
    }
    .message-bubble {
        padding: 1rem;
        border-radius: 1rem;
        margin-bottom: 1rem;
        max-width: 80%;
    }
    .message-user {
        background-color: #3b82f6;
        color: white;
        margin-left: auto;
        border-bottom-right-radius: 0.25rem;
    }
    .message-bot {
        background-color: #f3f4f6;
        color: #1f2937;
        margin-right: auto;
        border-bottom-left-radius: 0.25rem;
    }
    .product-card {
        background-color: white;
        border: 1px solid #e5e7eb;
        border-radius: 0.75rem;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .product-title {
        font-weight: 600;
        color: #111827;
        margin-bottom: 0.5rem;
    }
    .product-price {
        font-size: 1.25rem;
        font-weight: 700;
        color: #059669;
    }
    .typing-indicator {
        display: flex;
        gap: 0.25rem;
        padding: 1rem;
    }
    .typing-dot {
        width: 8px;
        height: 8px;
        background-color: #9ca3af;
        border-radius: 50%;
        animation: typing 1.4s infinite;
    }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
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

# Welcome Screen
if st.session_state.stage == "welcome":
    st.markdown('<h1 class="welcome-title">Hola, soy tu asesor experto en computadores 👋</h1>', unsafe_allow_html=True)
    st.markdown('<p class="welcome-subtitle">Encuentra tu portátil ideal sin tecnicismos. Cuéntame lo que buscas como si se lo contaras a un amigo.</p>', unsafe_allow_html=True)
    
    # Suggestion pills
    st.markdown("""
        <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; margin: 2rem 0;">
    """, unsafe_allow_html=True)
    
    suggestions = [
        "💻 Laptop para estudio",
        "🎮 Laptop para gaming", 
        "💼 Laptop para oficina",
        "✈️ Laptop ligera para viajar",
        "🔋 Laptop con buena batería"
    ]
    
    cols = st.columns(3)
    for i, suggestion in enumerate(suggestions):
        with cols[i % 3]:
            if st.button(suggestion, key=f"suggest_{i}", use_container_width=True):
                st.session_state.messages.append({"role": "user", "content": suggestion.replace("💻 ", "").replace("🎮 ", "").replace("💼 ", "").replace("✈️ ", "").replace("🔋 ", "")})
                st.session_state.stage = "chat"
                st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

# Chat Interface
if st.session_state.stage == "chat":
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    # Display messages
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="message-bubble message-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            if msg.get("type") == "products":
                # Product cards
                for product in msg["products"]:
                    st.markdown(f'''
                        <div class="product-card">
                            <div class="product-title">{product["name"]}</div>
                            <div class="product-price">${product["price_sale"]:,} COP</div>
                            <div style="margin-top: 0.5rem; color: #6b7280; font-size: 0.9rem;">
                                💾 {product.get("ram", "N/A")} | ⚖️ {product.get("weight_kg", "N/A")} kg | 🔋 {product.get("battery_hours", "N/A")}h
                            </div>
                        </div>
                    ''', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="message-bubble message-bot">{msg["content"]}</div>', unsafe_allow_html=True)
    
    # Quick reply suggestions
    if len(st.session_state.messages) > 0 and st.session_state.messages[-1]["role"] == "assistant":
        st.markdown("<div style='margin: 1rem 0; text-align: center;'>", unsafe_allow_html=True)
        st.caption("Sugerencias:")
        
        quick_replies = [
            "Más barato",
            "Más ligero", 
            "Más potente",
            "Ver alternativas"
        ]
        
        cols = st.columns(4)
        for i, reply in enumerate(quick_replies):
            with cols[i]:
                if st.button(reply, key=f"quick_{i}_{len(st.session_state.messages)}", use_container_width=True):
                    process_message(reply)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Chat input at bottom
if st.session_state.stage == "chat":
    with st.container():
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_input("Escribe tu mensaje...", key="chat_input", label_visibility="collapsed")
        with col2:
            if st.button("➤", use_container_width=True):
                if user_input:
                    process_message(user_input)
                    st.rerun()

def process_message(message):
    """Process user message and generate response"""
    st.session_state.messages.append({"role": "user", "content": message})
    
    # Show typing indicator
    with st.spinner("Pensando..."):
        time.sleep(0.5)
        
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
        
        # Build filters based on context
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
                
                # Add product cards
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
                "content": f"❌ Lo siento, tuve un problema buscando: {str(e)}"
            })

# Footer
st.markdown("---")
st.caption("Alkosto AI Assistant v0.2 | Interface conversacional")
