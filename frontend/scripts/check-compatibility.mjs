#!/usr/bin/env node
/**
 * Script de verificación de compatibilidad Frontend ↔ Backend
 * Ejecutar: node check-compatibility.mjs
 */

const BACKEND_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000';

console.log('🔍 Verificando compatibilidad Frontend ↔ Backend...\n');
console.log(`📡 Backend URL: ${BACKEND_URL}\n`);

const checks = [];

// Helper para hacer requests
async function testEndpoint(name, path, options = {}) {
  try {
    const url = `${BACKEND_URL}${path}`;
    const response = await fetch(url, options);
    const data = await response.json();
    
    return {
      name,
      status: response.ok ? '✅' : '❌',
      statusCode: response.status,
      ok: response.ok,
      data,
    };
  } catch (error) {
    return {
      name,
      status: '❌',
      statusCode: 0,
      ok: false,
      error: error.message,
    };
  }
}

// Test 1: Health endpoint
console.log('1️⃣  Probando endpoint /health...');
const healthCheck = await testEndpoint('Health Check', '/health');
checks.push(healthCheck);

if (healthCheck.ok) {
  console.log(`   ${healthCheck.status} Estado: ${healthCheck.data.status}`);
  console.log(`   📊 Chunks indexados: ${healthCheck.data.chunks_count}`);
  console.log(`   🤖 LLM cargado: ${healthCheck.data.llm_loaded ? 'Sí' : 'No'}`);
  console.log(`   📚 Índice existe: ${healthCheck.data.index_exists ? 'Sí' : 'No'}`);
} else {
  console.log(`   ${healthCheck.status} Error: ${healthCheck.error || healthCheck.statusCode}`);
}
console.log();

// Test 2: Stats endpoint
console.log('2️⃣  Probando endpoint /stats...');
const statsCheck = await testEndpoint('Stats', '/stats');
checks.push(statsCheck);

if (statsCheck.ok) {
  console.log(`   ${statsCheck.status} Documentos: ${statsCheck.data.total_documents}`);
  console.log(`   📄 Total chunks: ${statsCheck.data.total_chunks}`);
  console.log(`   📏 Avg chunk size: ${statsCheck.data.avg_chunk_size.toFixed(0)} chars`);
} else {
  console.log(`   ${statsCheck.status} Error: ${statsCheck.error || statsCheck.statusCode}`);
}
console.log();

// Test 3: Sources endpoint
console.log('3️⃣  Probando endpoint /sources...');
const sourcesCheck = await testEndpoint('Sources', '/sources');
checks.push(sourcesCheck);

if (sourcesCheck.ok) {
  const sources = sourcesCheck.data.sources || [];
  console.log(`   ${sourcesCheck.status} Fuentes disponibles: ${sources.length}`);
  if (sources.length > 0) {
    console.log(`   📁 Ejemplos: ${sources.slice(0, 3).join(', ')}`);
  }
} else {
  console.log(`   ${sourcesCheck.status} Error: ${sourcesCheck.error || sourcesCheck.statusCode}`);
}
console.log();

// Test 4: Cache stats endpoint
console.log('4️⃣  Probando endpoint /cache/stats...');
const cacheCheck = await testEndpoint('Cache Stats', '/cache/stats');
checks.push(cacheCheck);

if (cacheCheck.ok) {
  console.log(`   ${cacheCheck.status} Tamaño caché: ${cacheCheck.data.size}/${cacheCheck.data.max_size}`);
  console.log(`   🎯 Hit rate: ${(cacheCheck.data.hit_rate * 100).toFixed(1)}%`);
  console.log(`   ✅ Hits: ${cacheCheck.data.total_hits} | ❌ Misses: ${cacheCheck.data.total_misses}`);
} else {
  console.log(`   ${cacheCheck.status} Error: ${cacheCheck.error || cacheCheck.statusCode}`);
}
console.log();

// Test 5: Validación de request /ask (sin enviar realmente)
console.log('5️⃣  Verificando validación de /ask...');
const askValidationCheck = await testEndpoint(
  'Ask Validation', 
  '/ask',
  {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: 'ab' }), // Menos de 3 caracteres
  }
);
checks.push(askValidationCheck);

if (askValidationCheck.statusCode === 422) {
  console.log(`   ✅ Validación funcionando (rechazó pregunta < 3 chars)`);
  if (askValidationCheck.data?.detail) {
    console.log(`   📝 Mensaje: ${JSON.stringify(askValidationCheck.data.detail).slice(0, 100)}...`);
  }
} else if (askValidationCheck.statusCode === 429) {
  console.log(`   ⚠️  Rate limit activo (429) - Backend protegido ✅`);
} else {
  console.log(`   ❌ Validación NO funcionó correctamente (código: ${askValidationCheck.statusCode})`);
}
console.log();

// Resumen
console.log('━'.repeat(60));
console.log('📊 RESUMEN DE COMPATIBILIDAD\n');

const passed = checks.filter(c => c.ok || c.statusCode === 422 || c.statusCode === 429).length;
const total = checks.length;

console.log(`Pruebas exitosas: ${passed}/${total}`);

if (passed === total) {
  console.log('\n✅ El backend está funcionando correctamente');
  console.log('✅ Todos los endpoints responden como se espera');
  console.log('✅ El frontend es COMPATIBLE sin cambios');
  console.log('\n🚀 Puedes arrancar el frontend con: npm run dev');
} else if (passed >= 3) {
  console.log('\n⚠️  El backend funciona pero algunos endpoints nuevos no responden');
  console.log('✅ El frontend básico es COMPATIBLE');
  console.log('⚠️  Funciones avanzadas (stats, cache) podrían no funcionar');
} else {
  console.log('\n❌ El backend no está respondiendo correctamente');
  console.log('❌ Verifica que el servidor esté corriendo en:', BACKEND_URL);
  console.log('\n💡 Inicia el backend con: uvicorn app:app --reload --port 8000');
}

console.log('\n' + '━'.repeat(60));
console.log('📚 Para más información, lee: frontend/COMPATIBILIDAD_RESUMEN.md');
console.log('━'.repeat(60));

process.exit(passed >= 3 ? 0 : 1);
