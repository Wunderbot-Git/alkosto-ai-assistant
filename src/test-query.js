#!/usr/bin/env node
// Test-Modus: Zeigt die generierte Algolia-Query ohne sie auszuführen

const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

console.log('\n🔍 Alkosto Beratung - Query Generator Test\n');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

// Simuliere Bedarfsanalyse
const requirements = {};

askQuestions();

function askQuestions() {
  rl.question('🎯 Use Case (estudio/oficina/gaming/diseno): ', (useCase) => {
    requirements.useCase = useCase || 'estudio';
    
    rl.question('💰 Budget max (COP, z.B. 3000000): ', (budget) => {
      requirements.budget = parseInt(budget) || 3000000;
      
      rl.question('⚡ Prioritäten (komma-separiert: rendimiento,portabilidad,bateria,precio): ', (priorities) => {
        requirements.priorities = priorities ? priorities.split(',').map(p => p.trim()) : ['precio'];
        
        // Generiere Query
        const result = generateQuery(requirements);
        
        console.log('\n📋 ERFASSTE ANFORDERUNGEN:\n');
        console.log(JSON.stringify(requirements, null, 2));
        
        console.log('\n🔧 GENERIERTE ALGOLIA QUERY:\n');
        console.log('┌─────────────────────────────────────────────────────────────┐');
        console.log('│  Algolia Search Parameters                                  │');
        console.log('├─────────────────────────────────────────────────────────────┤');
        console.log(`│  Query:       "${result.query}"`);
        console.log(`│  Filters:     "${result.filters}"`);
        console.log(`│  Hits/Page:   ${result.hitsPerPage}`);
        console.log('└─────────────────────────────────────────────────────────────┘');
        
        console.log('\n📊 FILTER-ERKLÄRUNG:\n');
        result.filterExplanation.forEach(exp => console.log(`  • ${exp}`));
        
        console.log('\n✅ Diese Query würde an Algolia gesendet werden:');
        console.log('\n  POST /1/indexes/test_Philipp/query');
        console.log('  {');
        console.log(`    "query": "${result.query}",`);
        console.log(`    "filters": "${result.filters}",`);
        console.log(`    "hitsPerPage": ${result.hitsPerPage}`);
        console.log('  }');
        
        rl.question('\n💡 Mit echten Daten testen? (j/n): ', (answer) => {
          if (answer.toLowerCase() === 'j') {
            runRealSearch(result);
          } else {
            console.log('\n👋 Test beendet.\n');
            rl.close();
          }
        });
      });
    });
  });
}

function generateQuery(req) {
  const result = {
    filterExplanation: [],
    hitsPerPage: 5
  };
  
  // Query basierend auf Use Case
  let query = 'laptop';
  const useCase = req.useCase.toLowerCase();
  
  if (useCase.includes('estudio')) {
    query = 'laptop estudiante';
    result.filterExplanation.push('Query: "laptop estudiante" (optimiert für Studenten)');
  } else if (useCase.includes('oficina') || useCase.includes('office')) {
    query = 'laptop oficina';
    result.filterExplanation.push('Query: "laptop oficina" (optimiert für Büro)');
  } else if (useCase.includes('gaming')) {
    query = 'laptop gaming';
    result.filterExplanation.push('Query: "laptop gaming" (Gaming-spezifisch)');
  } else if (useCase.includes('diseno') || useCase.includes('creative')) {
    query = 'laptop diseño';
    result.filterExplanation.push('Query: "laptop diseño" (für Design/Content Creation)');
  } else {
    result.filterExplanation.push(`Query: "${query}" (allgemein)`);
  }
  
  result.query = query;
  
  // Baue Filter
  let filters = [];
  
  // Budget Filter
  filters.push(`price_sale < ${req.budget}`);
  result.filterExplanation.push(`Budget: price_sale < ${req.budget.toLocaleString()} COP`);
  
  // In Stock
  filters.push('in_stock:true');
  result.filterExplanation.push('Verfügbarkeit: in_stock:true');
  
  // Portabilität
  if (req.priorities.includes('portabilidad') || req.priorities.includes('portable')) {
    filters.push('weight_kg < 1.5');
    result.filterExplanation.push('Portabilität: weight_kg < 1.5 kg (leicht)');
  }
  
  // Akku
  if (req.priorities.includes('bateria') || req.priorities.includes('battery')) {
    filters.push('battery_hours > 10');
    result.filterExplanation.push('Akku: battery_hours > 10 Stunden (lang)');
  }
  
  // Rendimiento → RAM
  if (req.priorities.includes('rendimiento') || req.priorities.includes('performance')) {
    // In echt: ram:'16 GB' OR ram:'32 GB'
    // Für Demo vereinfacht
    result.filterExplanation.push('Performance: RAM-Preference (16GB+ empfohlen)');
  }
  
  result.filters = filters.join(' AND ');
  
  return result;
}

async function runRealSearch(queryParams) {
  console.log('\n🔍 Führe echte Suche durch...\n');
  
  const { searchProducts } = require('./algoliaClient');
  
  try {
    const result = await searchProducts({
      query: queryParams.query,
      filters: queryParams.filters,
      hitsPerPage: queryParams.hitsPerPage
    });
    
    console.log(`✅ ${result.hits.length} Produkte gefunden!\n`);
    
    if (result.hits.length > 0) {
      console.log('📦 ERGEBNISSE:\n');
      result.hits.forEach((hit, i) => {
        console.log(`${i + 1}. ${hit.name}`);
        console.log(`   💰 ${hit.price_sale?.toLocaleString()} COP | 💾 ${hit.ram || 'N/A'} | ⚖️ ${hit.weight_kg || 'N/A'} kg`);
      });
    }
    
    console.log('\n');
    
  } catch (error) {
    console.error('❌ Fehler:', error.message);
    console.log('\n💡 Tipp: Füge ALGOLIA_API_KEY in .env ein für echte Daten\n');
  }
  
  rl.close();
}
