import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, AlertTriangle, CheckCircle, Clock, ExternalLink, Shield, Zap } from 'lucide-react';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || '/api';

// Thermometer Component
const SuspicionThermometer = ({ score, isAnimating }) => {
  const getThermometerColor = (score) => {
    if (score <= 30) return 'bg-trust-gradient';
    if (score <= 60) return 'bg-caution-gradient';
    return 'bg-danger-gradient';
  };

  const getThermometerLabel = (score) => {
    if (score <= 30) return { text: 'Baixa Suspeita', color: 'text-trust-green', icon: CheckCircle };
    if (score <= 60) return { text: 'Suspeita Moderada', color: 'text-caution-yellow', icon: AlertTriangle };
    return { text: 'Alta Suspeita', color: 'text-danger-red', icon: AlertTriangle };
  };

  const fillHeight = `${score}%`;
  const label = getThermometerLabel(score);
  const IconComponent = label.icon;

  return (
    <div className="flex flex-col items-center space-y-4">
      {/* Score Display */}
      <div className="text-center">
        <motion.div 
          className="text-6xl font-bold text-white mb-2"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.5, type: "spring", stiffness: 200 }}
        >
          {isAnimating ? (
            <span className="animate-pulse">--</span>
          ) : (
            score
          )}
        </motion.div>
        <div className={`flex items-center justify-center space-x-2 ${label.color}`}>
          <IconComponent size={20} />
          <span className="font-semibold text-lg">{label.text}</span>
        </div>
      </div>

      {/* Linear Vertical Thermometer */}
      <div className="relative">
        <div 
          className="thermometer-container w-16 h-80 mx-auto"
          style={{ background: 'rgba(255, 255, 255, 0.1)' }}
        >
          {/* Scale markings */}
          <div className="absolute left-0 top-0 h-full w-full">
            {[0, 25, 50, 75, 100].map((mark) => (
              <div
                key={mark}
                className="absolute left-0 w-full border-t border-white border-opacity-30"
                style={{ bottom: `${mark}%` }}
              >
                <span className="absolute -left-8 -top-2 text-xs text-white font-medium">
                  {mark}
                </span>
              </div>
            ))}
          </div>

          {/* Thermometer fill */}
          <motion.div
            className={`thermometer-fill ${getThermometerColor(score)}`}
            initial={{ height: '0%' }}
            animate={{ height: isAnimating ? '0%' : fillHeight }}
            transition={{ 
              duration: 1.5, 
              delay: 0.8,
              ease: [0.4, 0, 0.2, 1]
            }}
          />

          {/* Animated bubbles effect */}
          {!isAnimating && score > 0 && (
            <div className="absolute inset-0 overflow-hidden">
              {[...Array(3)].map((_, i) => (
                <motion.div
                  key={i}
                  className="absolute w-2 h-2 bg-white rounded-full opacity-30"
                  style={{
                    left: `${20 + i * 20}%`,
                    bottom: `${Math.min(score - 10, 5)}%`
                  }}
                  animate={{
                    y: [0, -20, 0],
                    opacity: [0.3, 0.7, 0.3]
                  }}
                  transition={{
                    duration: 2,
                    delay: i * 0.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Scale labels */}
        <div className="absolute -right-20 top-0 h-full flex flex-col justify-between text-xs text-white font-medium">
          <span className="flex items-center">
            <AlertTriangle size={14} className="text-danger-red mr-1" />
            Crítica
          </span>
          <span className="flex items-center">
            <AlertTriangle size={14} className="text-caution-yellow mr-1" />
            Moderada
          </span>
          <span className="flex items-center">
            <CheckCircle size={14} className="text-trust-green mr-1" />
            Confiável
          </span>
        </div>
      </div>
    </div>
  );
};

// Factor List Component
const FactorsList = ({ factors }) => {
  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
        <Shield className="mr-2 text-dark-blue" size={20} />
        Fatores Analisados
      </h3>
      <div className="space-y-2">
        {factors.map((factor, index) => (
          <motion.div
            key={index}
            className="factor-item bg-white bg-opacity-50 rounded-lg p-3 border-l-4 border-dark-blue"
            style={{ '--delay': `${index * 0.1}s` }}
          >
            <p className="text-sm text-gray-700 leading-relaxed">{factor}</p>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

// Sources Component
const SourcesList = ({ sources }) => {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
        <ExternalLink className="mr-2 text-dark-blue" size={20} />
        Fontes Verificadas
      </h3>
      <div className="space-y-2">
        {sources.slice(0, 5).map((source, index) => (
          <motion.a
            key={index}
            href={source}
            target="_blank"
            rel="noopener noreferrer"
            className="block bg-white bg-opacity-50 rounded-lg p-3 hover:bg-opacity-70 transition-all duration-200 border border-gray-200"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <p className="text-sm text-dark-blue hover:underline truncate">
              {new URL(source).hostname}
            </p>
          </motion.a>
        ))}
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const [inputValue, setInputValue] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleAnalyze = async () => {
    if (!inputValue.trim()) {
      setError('Por favor, insira um link ou texto para análise');
      return;
    }

    setIsAnalyzing(true);
    setError('');
    setResult(null);

    try {
      const response = await axios.post(`${API_BASE_URL}/api/analyze`, {
        url_or_text: inputValue.trim()
      }, {
        timeout: 60000 // 60 seconds timeout for scraping
      });

      setResult(response.data);
    } catch (err) {
      console.error('Erro na análise:', err);
      if (err.code === 'ECONNABORTED') {
        setError('Análise demorou muito para ser concluída. Tente novamente.');
      } else if (err.response?.data?.detail) {
        setError(err.response.data.detail);
      } else {
        setError('Erro ao analisar. Verifique sua conexão e tente novamente.');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isAnalyzing) {
      handleAnalyze();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-blue-800">
      {/* Header */}
      <header className="relative z-10 pt-8 pb-6">
        <div className="container mx-auto px-4 text-center">
          <motion.div
            initial={{ opacity: 0, y: -30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <div className="flex items-center justify-center space-x-3 mb-4">
              <div className="p-3 bg-white bg-opacity-20 rounded-full">
                <Zap className="text-white" size={40} />
              </div>
              <h1 className="text-5xl font-bold text-white">
                Fake News <span className="text-yellow-300">Sniff</span>
              </h1>
            </div>
            <p className="text-xl text-gray-200 font-medium">
              Seu filtro contra desinformação
            </p>
          </motion.div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 pb-12">
        <div className="max-w-6xl mx-auto">
          {/* Input Section */}
          <motion.div
            className="glass rounded-2xl p-8 mb-8"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <div className="max-w-2xl mx-auto">
              <div className="relative mb-6">
                <textarea
                  className="w-full px-6 py-4 pr-16 text-lg bg-white bg-opacity-90 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-2 focus:ring-blue-200 resize-none transition-all duration-200"
                  placeholder="Cole aqui o link da notícia ou texto que deseja verificar..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  rows={4}
                  disabled={isAnalyzing}
                />
                <Search className="absolute right-4 top-4 text-gray-400" size={24} />
              </div>

              <motion.button
                className="btn-analyze w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white font-bold py-4 px-8 rounded-xl text-lg shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                whileTap={{ scale: 0.98 }}
                transition={{ type: "spring", stiffness: 400, damping: 17 }}
              >
                {isAnalyzing ? (
                  <div className="flex items-center justify-center space-x-3">
                    <div className="spinner"></div>
                    <span>Analisando notícia...</span>
                  </div>
                ) : (
                  <div className="flex items-center justify-center space-x-3">
                    <Search size={20} />
                    <span>Analisar Credibilidade</span>
                  </div>
                )}
              </motion.button>

              {error && (
                <motion.div
                  className="mt-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                >
                  <div className="flex items-center">
                    <AlertTriangle className="mr-2" size={20} />
                    {error}
                  </div>
                </motion.div>
              )}
            </div>
          </motion.div>

          {/* Results Section */}
          <AnimatePresence>
            {(result || isAnalyzing) && (
              <motion.div
                className="grid lg:grid-cols-2 gap-8"
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.6 }}
              >
                {/* Thermometer Section */}
                <div className="glass rounded-2xl p-8 flex items-center justify-center">
                  <SuspicionThermometer 
                    score={result?.suspicion_score || 0} 
                    isAnimating={isAnalyzing}
                  />
                </div>

                {/* Details Section */}
                <div className="space-y-6">
                  {result && (
                    <>
                      {/* Content Summary */}
                      <div className="glass rounded-2xl p-6">
                        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
                          <Clock className="mr-2 text-dark-blue" size={20} />
                          Resumo da Análise
                        </h3>
                        <p className="text-gray-700 leading-relaxed">
                          {result.content_summary}
                        </p>
                      </div>

                      {/* Factors */}
                      <div className="glass rounded-2xl p-6">
                        <FactorsList factors={result.factors} />
                      </div>

                      {/* Sources */}
                      {result.sources_checked && result.sources_checked.length > 0 && (
                        <div className="glass rounded-2xl p-6">
                          <SourcesList sources={result.sources_checked} />
                        </div>
                      )}
                    </>
                  )}

                  {isAnalyzing && (
                    <div className="glass rounded-2xl p-6">
                      <div className="flex items-center justify-center space-x-3 text-gray-600">
                        <div className="spinner"></div>
                        <span className="text-lg">Verificando fontes...</span>
                      </div>
                      <div className="mt-4 space-y-2">
                        {[...Array(3)].map((_, i) => (
                          <div key={i} className="shimmer h-4 rounded" />
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-black bg-opacity-20 backdrop-filter backdrop-blur-sm py-6 mt-12">
        <div className="container mx-auto px-4 text-center">
          <p className="text-gray-200 text-sm leading-relaxed max-w-2xl mx-auto">
            ⚠️ <strong>Importante:</strong> Esta ferramenta não rotula notícias como verdadeiras ou falsas, 
            apenas indica sinais de suspeita baseados em verificação cruzada de fontes. 
            Use sempre seu senso crítico e consulte múltiplas fontes confiáveis.
          </p>
          <div className="mt-4 text-gray-300 text-xs">
            Desenvolvido para combater a desinformação • Fake News Sniff © 2024
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;