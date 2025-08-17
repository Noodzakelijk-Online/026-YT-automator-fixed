import React from 'react';
import YouTubeAutomation from '../components/YouTubeAutomation';

const Index = () => {
  return (
    <div className="min-h-screen bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-center text-gray-900 mb-8">YouTube Automation Tool</h1>
        <YouTubeAutomation />
      </div>
    </div>
  );
};

export default Index;