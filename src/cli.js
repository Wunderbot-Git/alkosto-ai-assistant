#!/usr/bin/env node
// CLI Prototyp für Alkosto AI Assistant

const readline = require('readline');
const { searchProducts } = require('./algoliaClient');
const systemPrompt = require('./prompts/systemPrompt');

// Simulierter Conversation State
const conversationState = {
  stage: 'greeting', // greeting, requirements, searching, recommendation, done
  requirements: {
    useCase: null,
    budget: null,
    priorities: [],
    mustHaves: {}
  },
  history: []
};

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('\n🤖 Alkosto AI Sales Assistant\n');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
console.log('👋 ¡Hola! Soy tu asistente de ventas de Alkosto.');
console.log('   Te ayudaré a encontrar el laptop perfecto para ti.\n');

askQuestion();

function askQuestion() {
  switch (conversationState.stage) {
    case 'greeting':
      rl.question('📝 ¿Para qué usarás principalmente el laptop? (ej: estudio, oficina, gaming, diseño): ', (answer) => {
        conversationState.requirements.useCase = answer || 'estudio';
        conversationState.stage = 'budget';
        conversationState.history.push({ role: 'user', content: answer });
        askQuestion();
      });
      break;

    case 'budget':
      rl.question('💰 ¿Cuál es tu presupuesto máximo? (en COP, ej: 3000000): ', (answer) => {
        const budget = parseInt(answer) || 3000000;
        conversationState.requirements.budget = budget;
        conversationState.stage = 'priorities';
        conversationState.history.push({ role: 'user', content: answer });
        askQuestion();
      });
      break;

    case 'priorities':
      rl.question('⚡ ¿Qué es más importante para ti? (rendimiento, portabilidad, bateria, precio): ', (answer) => {
        conversationState.requirements.priorities = answer ? answer.split(',').map(p => p.trim()) : ['precio'];
        conversationState.stage = 'searching';
        conversationState.history.push({ role: 'user', content: answer });
        performSearch();
      });
      break;

    case 'recommendation':
      rl.question('\n❓ ¿Te gustaría ajustar la búsqueda o saber más de alguna opción? (s/n): ', (answer) => {
        if (answer.toLowerCase() === 's' || answer.toLowerCase() === 'si') {
          conversationState.stage = 'greeting';
          console.log('\n🔄 OK, empecemos de nuevo...\n');
          askQuestion();
        } else {
          console.log('\n👋 ¡Gracias por usar Alkosto AI Assistant! Hasta pronto.\n');
          rl.close();
        }
      });
      break;
  }
}

async function performSearch() {
  const { useCase, budget, priorities } = conversationState.requirements;
  
  console.log('\n🔍 Buscando laptops...');
  console.log(`   Uso: ${useCase}`);
  console.log(`   Budget: ${budget.toLocaleString()} COP`);
  console.log(`   Prioridades: ${priorities.join(', ')}\n`);

  // Baue Filter-String
  let filters = `price_sale < ${budget} AND in_stock:true`;
  
  // Gewicht-Priorität für Portabilität
  if (priorities.includes('portabilidad')) {
    filters += ' AND weight_kg < 1.5';
  }
  
  // Akku-Priorität
  if (priorities.includes('bateria')) {
    filters += ' AND battery_hours > 10';
  }

  // Query basierend auf Use Case
  let query = 'laptop';
  if (useCase.toLowerCase().includes('estudio')) query = 'laptop estudiante';
  if (useCase.toLowerCase().includes('gaming')) query = 'laptop gaming';
  if (useCase.toLowerCase().includes('oficina')) query = 'laptop oficina';

  try {
    const result = await searchProducts({
      query,
      filters,
      hitsPerPage: 5
    });

    if (result.hits.length === 0) {
      console.log('❌ No se encontraron laptops con esos criterios.');
      console.log('   Intenta con un presupuesto mayor o diferentes prioridades.\n');
      conversationState.stage = 'recommendation';
      askQuestion();
      return;
    }

    displayRecommendations(result.hits, priorities);
    conversationState.stage = 'recommendation';
    askQuestion();

  } catch (error) {
    console.error('❌ Error en la búsqueda:', error.message);
    conversationState.stage = 'recommendation';
    askQuestion();
  }
}

function displayRecommendations(products, priorities) {
  console.log('\n📊 RESULTADOS DE BÚSQUEDA\n');
  console.log(`Se encontraron ${products.length} opciones:\n`);

  // Beste Option: erstes Produkt
  const best = products[0];
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log('🏆 MEJOR OPCIÓN');
  console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
  console.log(`📱 ${best.name}`);
  console.log(`🏢 Marca: ${best.brand}`);
  console.log(`💵 Precio: ${best.price_sale?.toLocaleString()} COP`);
  console.log(`💾 RAM: ${best.ram || 'N/A'}`);
  console.log(`🧠 Procesador: ${best.processor || best.processor_brand || 'N/A'}`);
  if (best.weight_kg) console.log(`⚖️  Peso: ${best.weight_kg} kg`);
  if (best.battery_hours) console.log(`🔋 Batería: ${best.battery_hours} horas`);
  console.log(`📦 Stock: ${best.stock || 'Disponible'}`);
  
  if (best.key_features && Array.isArray(best.key_features)) {
    console.log('\n✨ Características destacadas:');
    best.key_features.slice(0, 3).forEach(f => console.log(`   • ${f}`));
  }
  
  if (best.url) console.log(`\n🔗 ${best.url}`);

  // Alternative: zweites Produkt (falls vorhanden)
  if (products.length > 1) {
    const alt = products[1];
    console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log('🥈 ALTERNATIVA');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
    console.log(`📱 ${alt.name}`);
    console.log(`🏢 Marca: ${alt.brand}`);
    console.log(`💵 Precio: ${alt.price_sale?.toLocaleString()} COP`);
    console.log(`💾 RAM: ${alt.ram || 'N/A'}`);
    if (alt.weight_kg) console.log(`⚖️  Peso: ${alt.weight_kg} kg`);
    if (alt.battery_hours) console.log(`🔋 Batería: ${alt.battery_hours} horas`);
    if (alt.url) console.log(`🔗 ${alt.url}`);
  }

  console.log('\n');
}
