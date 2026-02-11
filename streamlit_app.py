import streamlit as st
import json
from datetime import datetime
from algolia_client import get_client, DEMO_PRODUCTS

# Page config
st.set_page_config(
    page_title="Alkosto AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize client
client = get_client()

# CSS Styling
st.markdown("""
<style>
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .chat-message.user {
        background-color: #1e3a5f;
    }
    .chat-message.bot {
        background-color: #2d3748;
    }
    .product-card {
        background-color: #1a202c;
        border-radius: 0.75rem;
        padding: 1rem;
        border: 1px solid #4a5568;
        margin-bottom: 1rem;
    }
    .best-choice {
        border: 2px solid #48bb78;
    }
    .alt-choice {
        border: 2px solid #ed8936;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🤖 Alkosto AI")
    st.subheader("Tu asistente de laptops")
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuración")
    
    use_case = st.selectbox(
        "🎯 ¿Para qué lo usarás?",
        ["estudio", "oficina", "gaming", "diseño", "uso general"],
        index=0
    )
    
    budget = st.slider(
        "💰 Presupuesto máximo (COP)",
        min_value=1500000,
        max_value=5000000,
        value=2500000,
        step=100000
    )
    st.markdown(f"**{budget:,} COP**")
    
    st.markdown("### ⚡ Prioridades")
    priority_portable = st.checkbox("Portabilidad (ligero)", value=False)
    priority_battery = st.checkbox("Batería (larga duración)", value=False)
    
    st.markdown("---")
    
    if st.button("🔄 Nueva búsqueda", type="primary"):
        st.session_state.messages = []
        st.session_state.stage = "greeting"
        st.rerun()
    
    # Show mode indicator
    if client.is_demo_mode:
        st.warning("⚠️ Modo Demo: Usando datos de ejemplo")
    else:
        st.success("✅ Conectado a Algolia")

# Main content
st.title("💬 Chat con Alkosto AI")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.stage = "greeting"

# Show chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Initial greeting
if len(st.session_state.messages) == 0:
    welcome = """
    👋 ¡Hola! Soy tu asistente de ventas de **Alkosto**.
    
    Configura tu búsqueda en el panel izquierdo y escribe un mensaje para empezar.
    
    Por ejemplo: *"Busco un laptop para estudio, ligero y con buena batería"*
    """
    st.session_state.messages.append({"role": "assistant", "content": welcome})
    with st.chat_message("assistant"):
        st.markdown(welcome)

# Chat input
if prompt := st.chat_input("Escribe tu mensaje..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and show response
    with st.chat_message("assistant"):
        with st.spinner("Buscando laptops..."):
            # Build filters
            filters = [f"price_sale < {budget}", "in_stock:true"]
            filter_desc = [f"💰 Menos de {budget:,} COP"]
            
            if priority_portable:
                filters.append("weight_kg < 1.5")
                filter_desc.append("⚖️ Menos de 1.5 kg")
            
            if priority_battery:
                filters.append("battery_hours > 10")
                filter_desc.append("🔋 Más de 10 horas")
            
            # Build query
            query_map = {
                "estudio": "laptop estudiante",
                "oficina": "laptop oficina",
                "gaming": "laptop gaming",
                "diseño": "laptop diseño"
            }
            query = query_map.get(use_case, "laptop")
            
            # Search
            try:
                result = client.search_products({
                    "query": query,
                    "filters": " AND ".join(filters),
                    "hits_per_page": 5
                })
                
                # Build response
                response = f"""🔍 **Buscando laptops para {use_case}...**

**Filtros aplicados:**
{" • ".join(filter_desc)}

**{result['total']} laptops encontrados**"""
                
                if result["hits"]:
                    # Best choice
                    best = result["hits"][0]
                    response += f"""

---

🏆 **MEJOR OPCIÓN: {best['name']}**

💵 **{best['price_sale']:,} COP** | 💾 {best.get('ram', 'N/A')} | ⚖️ {best.get('weight_kg', 'N/A')} kg

**Por qué es perfecto:**
"""
                    for feature in best.get('key_features', [])[:3]:
                        response += f"- ✨ {feature}\n"
                    
                    response += f"\n[Ver en Alkosto ↗]({best['url']})"
                    
                    # Alternative
                    if len(result["hits"]) > 1:
                        alt = result["hits"][1]
                        response += f"""

---

🥈 **ALTERNATIVA: {alt['name']}**

💵 {alt['price_sale']:,} COP | 💾 {alt.get('ram', 'N/A')}

[Ver en Alkosto ↗]({alt['url']})
"""
                else:
                    response += """

😕 No se encontraron laptops con esos criterios exactos.

💡 **Sugerencias:**
- Aumenta el presupuesto
- Reduce filtros (quita "ligero" o "batería")
"""
                
                response += "\n\n¿Te gustaría ajustar los filtros o saber más? 🤔"
                
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
                
            except Exception as e:
                error_msg = f"❌ Error en la búsqueda: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Footer
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("📊 Ver Analytics"):
        analytics = client.get_analytics()
        st.json(analytics)
with col2:
    st.caption("Alkosto AI Assistant v0.1")
