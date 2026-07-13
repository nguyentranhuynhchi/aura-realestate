import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import PredictPage from './features/predict/components/PredictPage';
import ChatbotPage from './features/chatbot/components/ChatbotPage';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-[#F8FAFC] flex flex-col text-[#0F172A]">
        {/* Header tối giản cao cấp */}
        <Header />
        
        {/* Khu vực nội dung chính */}
        <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8 md:py-12">
          <Routes>
            <Route path="/" element={<Navigate to="/predict" replace />} />
            <Route path="/predict" element={<PredictPage />} />
            <Route path="/chatbot" element={<ChatbotPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;