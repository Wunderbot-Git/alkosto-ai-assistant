# Streamlit App für Alkosto AI Sales Assistant
import streamlit as st
import json
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Alkosto AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Styling
st.markdown("""
<style>
.chat-message {
    padding: 1rem;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: flex-start;
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
.product-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #63b3ed;
    margin-bottom: 0.5rem;
}
.specs-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    margin-top: 0.5rem;
}
.spec-item {
    background-color: #2d3748;
    padding: 0.5rem;
    border-radius: 0.25rem;
    font-size: 0.9rem;
}
.best-choice {
    border: 2px solid #48bb78;
}
.alt-choice {
    border: 2px solid #ed8936;
}
</style>
""", unsafe_allow_html=True)

# Demo Produkte (gleiche wie in Node.js)
DEMO_PRODUCTS = [
    {
        "objectID": "demo-1",
        "name": "HP Laptop 15\" Intel Core i5 16GB RAM 512GB SSD",
        "brand": "HP",
        "price_sale": 2499000,
        "price_list": 2899000,
        "ram": "16 GB",
        "storage": "512 GB SSD",
        "processor": "Intel Core i5-1235U",
        "weight_kg": 1.69,
        "battery_hours": 8.0,
        "screen_size": "15.6 Pulgadas",
        "os": "Windows",
        "in_stock": True,
        "stock": 45,
        "key_features": [
            "Procesador Intel Core i5 de 12va generación",
            "16GB RAM para multitarea fluida",
            "Disco SSD 512GB de alta velocidad",
            "Pantalla Full HD de 15.6 pulgadas",
            "Windows 11 Home preinstalado"
        ],
        "url": "https://www.alkosto.com/laptop-hp-15-intel-core-i5",
        "image_1": "https://cdn.dam.alkosto.com/hp-laptop-15.jpg"
    },
    {
        "objectID": "demo-2",
        "name": "ASUS VivoBook 14\" AMD Ryzen 5 8GB RAM 256GB SSD",
        "brand": "ASUS",
        "price_sale": 1999000,
        "price_list": 2299000,
        "ram": "8 GB",
        "storage": "256 GB SSD",
        "processor": "AMD Ryzen 5 5500U",
        "weight_kg": 1.40,
        "battery_hours": 10.0,
        "screen_size": "14 Pulgadas",
        "os": "Windows",
        "in_stock": True,
        "stock": 23,
        "key_features": [
            "Diseño ultradelgado y ligero (1.4kg)",
            "Procesador AMD Ryzen 5 eficiente",
            "Pantalla NanoEdge con bordes delgados",
            "Teclado retroiluminado",
            "Batería de larga duración"
        ],
        "url": "https://www.alkosto.com/asus-vivobook-14-amd",
        "image_1": "https://cdn.dam.alkosto.com/asus-vivobook-14.jpg"
    },
    {
        "objectID": "demo-3",
        "name": "Lenovo IdeaPad 3 15.6\" Intel Core i3 8GB RAM 256GB SSD",
        "brand": "LENOVO",
        "price_sale": 1799000,
        "price_list": 1999000,
        "ram": "8 GB",
        "storage": "256 GB SSD",
        "processor": "Intel Core i3-1115G4",
        "weight_kg": 1.70,
        "battery_hours": 7.5,
        "screen_size": "15.6 Pulgadas",
        "os": "Windows",
        "in_stock": True,
        "stock": 67,
        "key_features": [
            "Excelente relación precio-rendimiento",
            "Pantalla HD antirreflejo",
            "Dolby Audio para mejor sonido",
            "Webcam con obturador de privacidad",
            "Ideal para estudiantes y oficina"
        ],
        "url": "https://www.alkosto.com/lenovo-ideapad-3-15",
        "image_1": "https://cdn.dam.alkosto.com/lenovo-ideapad-3.jpg"
    }
]

# Sidebar
with st.sidebar:
    st.title("🤖 Alkosto AI")
    st.subheader("Tu asistente de laptops")
    
    st.markdown("---")
    st.markdown("### ⚙️ Configuración")
    
    # Use Case
    use_case = st.selectbox(
        "🎯 ¿Para qué lo usarás?",
        ["estudio", "oficina", "gaming", "diseño", "uso general"],
        index=0
    )
    
    # Budget Slider
    budget = st.slider(
        "💰 Presupuesto máximo (COP)",
        min_value=1500000,
        max_value=5000000,
        value=2500000,
        step=100000,
        format="%d"
    )
    st.markdown(f"**{budget:,} COP**")
    
    # Priorities
    st.markdown("### ⚡ Prioridades")
    priority_portable = st.checkbox("Portabilidad (ligero)", value=False)
    priority_battery = st.checkbox("Batería (larga duración)", value=False)
    priority_performance = st.checkbox("Rendimiento", value=False)
    
    st.markdown("---")
    
    if st.button("🔄 Nueva búsqueda", type="primary"):
        st.session_state.messages = []
        st.session_state.stage = "greeting"
        st.rerun()

# Main content
st.title("💬 Chat con Alkosto AI")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.stage = "greeting"
    st.session_state.requirements = {}

# Greeting message
if len(st.session_state.messages) == 0:
    welcome_msg = """
    👋 ¡Hola! Soy tu asistente de ventas de **Alkosto**.
    
    Te ayudaré a encontrar el laptop perfecto para ti. Tengo acceso a **317 laptops y tablets** en nuestro catálogo.
    
    📋 Configura tu búsqueda en el panel izquierdo y haz clic en **Nueva búsqueda** para empezar.
    
    ¿Listo? 🚀
    """
    st.session_state.messages.append({"role": "assistant", "content": welcome_msg})

# Show chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Escribe tu mensaje..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Buscando laptops..."):
            # Simulate search delay
            import time
            time.sleep(0.5)
            
            # Generate search results
            response = generate_response(
                use_case, budget, 
                priority_portable, priority_battery, priority_performance
            )
            st.markdown(response)
    
    st.session_state.messages.append({"role": "assistant", "content": response})

def generate_response(use_case, budget, portable, battery, performance):
    """Generate search results based on requirements"""
    
    # Build filters
    filters = []
    filter_desc = []
    
    # Budget
    filters.append(lambda p: p["price_sale"] < budget)
    filter_desc.append(f"💰 Menos de {budget:,} COP")
    
    # Portability
    if portable:
        filters.append(lambda p: p["weight_kg"] < 1.5)
        filter_desc.append("⚖️ Menos de 1.5 kg")
    
    # Battery
    if battery:
        filters.append(lambda p: p["battery_hours"] > 10)
        filter_desc.append("🔋 Más de 10 horas de batería")
    
    # Apply filters
    results = DEMO_PRODUCTS.copy()
    results = [p for p in results if p["in_stock"]]
    for f in filters:
        results = [p for p in results if f(p)]
    
    # Sort by relevance (price ascending)
    results.sort(key=lambda x: x["price_sale"])
    
    # Build response
    response = f"""
    🔍 **Buscando laptops para {use_case}...**
    
    **Filtros aplicados:**
    {" • ".join(filter_desc)}
    
    ---
    """
    
    if len(results) == 0:
        response += """
        😕 **No encontramos laptops** con esos criterios exactos.
        
        💡 **Sugerencias:**
        - Aumenta el presupuesto
        - Reduce filtros (quita "ligero" o "batería")
        - Prueba con "uso general"
        """
    else:
        response += f"""
        ✅ **{len(results)} laptops encontrados**
        
        Aquí están las mejores opciones:
        """
        
        # Best option
        best = results[0]
        response += f"""
        ---
        
        🏆 **MEJOR OPCIÓN**
        
        ### {best['name']}
        
        💵 **{best['price_sale']:,} COP**
        
        **Especificaciones:**
        - 💾 RAM: {best['ram']}
        - 🧠 Procesador: {best['processor']}
        - ⚖️ Peso: {best['weight_kg']} kg
        - 🔋 Batería: {best['battery_hours']} horas
        - 📦 Stock: {best['stock']} unidades
        
        **Por qué es perfecto para ti:**
        """
        
        for feature in best['key_features'][:3]:
            response += f"- ✨ {feature}\n"
        
        response += f"""
        
        [Ver en Alkosto ↗]({best['url']})
        """
        
        # Alternative
        if len(results) > 1:
            alt = results[1]
            price_diff = best['price_sale'] - alt['price_sale']
            response += f"""
            
            ---
            
            🥈 **ALTERNATIVA (Ahorra {price_diff:,} COP)**
            
            ### {alt['name']}
            
            💵 **{alt['price_sale']:,} COP** 
            
            💾 {alt['ram']} | 🧠 {alt['processor']} | ⚖️ {alt['weight_kg']} kg
            
            [Ver en Alkosto ↗]({alt['url']})
            """
    
    response += """
    
    ---
    
    ¿Te gustaría **ajustar los filtros** en el panel izquierdo o **saber más** de alguna opción? 🤔
    """
    
    return response

