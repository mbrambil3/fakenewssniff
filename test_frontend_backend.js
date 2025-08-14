// Test script to verify frontend-backend communication
const axios = require('axios');

const API_BASE_URL = 'http://10.64.130.223:8001';
const TEST_URL = 'https://www.poder360.com.br/poder-internacional/trump-e-putin-discutirao-enorme-potencial-economico-em-encontro/';

console.log('🔍 Testing Frontend-Backend Communication');
console.log(`Backend URL: ${API_BASE_URL}`);
console.log(`Test URL: ${TEST_URL}`);
console.log('=' * 60);

async function testAnalyze() {
    try {
        console.log('📡 Sending POST request to /api/analyze...');
        
        const response = await axios.post(`${API_BASE_URL}/api/analyze`, {
            url_or_text: TEST_URL
        }, {
            timeout: 60000,
            headers: {
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3000',
                'User-Agent': 'Mozilla/5.0 (compatible; Test-Agent)'
            }
        });

        console.log('✅ SUCCESS!');
        console.log(`Status: ${response.status}`);
        console.log(`Suspicion Score: ${response.data.suspicion_score}`);
        console.log(`Factors: ${response.data.factors.length} found`);
        console.log(`Content Length: ${response.data.content_summary.length} chars`);
        console.log('First factor:', response.data.factors[0]);
        
        return true;
    } catch (error) {
        console.log('❌ FAILED!');
        console.log('Error type:', error.constructor.name);
        console.log('Error code:', error.code);
        console.log('Error message:', error.message);
        
        if (error.response) {
            console.log('Response status:', error.response.status);
            console.log('Response data:', error.response.data);
        }
        
        return false;
    }
}

async function testHealth() {
    try {
        console.log('🏥 Testing health endpoint...');
        const response = await axios.get(`${API_BASE_URL}/api/health`);
        console.log('✅ Health check passed:', response.data);
        return true;
    } catch (error) {
        console.log('❌ Health check failed:', error.message);
        return false;
    }
}

async function runTests() {
    console.log('Starting tests...\n');
    
    const healthOk = await testHealth();
    console.log('');
    
    if (healthOk) {
        const analyzeOk = await testAnalyze();
        console.log('');
        
        if (analyzeOk) {
            console.log('🎉 ALL TESTS PASSED! Frontend should work now.');
        } else {
            console.log('💥 ANALYZE TEST FAILED - This is the user\'s issue');
        }
    } else {
        console.log('💥 HEALTH CHECK FAILED - Backend not accessible');
    }
}

runTests();