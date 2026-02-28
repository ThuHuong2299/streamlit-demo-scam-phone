import React, { useEffect, useState } from 'react';

export default function ChemicalLoadingScreen() {
  const [bubbles, setBubbles] = useState([]);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Generate initial bubbles
    const initialBubbles = Array.from({ length: 8 }, (_, i) => ({
      id: i,
      x: Math.random() * 90 + 5,
      y: Math.random() * 90 + 5,
      size: Math.random() * 30 + 15,
      delay: Math.random() * 2,
      duration: Math.random() * 3 + 2,
    }));
    setBubbles(initialBubbles);

    // Simulate loading progress
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return prev + 1;
      });
    }, 50);

    return () => clearInterval(progressInterval);
  }, []);

  return (
    <div className="relative w-full h-screen overflow-hidden bg-gradient-to-br from-blue-100 via-purple-50 to-pink-100">
      {/* Floating bubbles */}
      {bubbles.map((bubble) => (
        <div
          key={bubble.id}
          className="absolute rounded-full border-2 border-pink-400 animate-float"
          style={{
            left: `${bubble.x}%`,
            top: `${bubble.y}%`,
            width: `${bubble.size}px`,
            height: `${bubble.size}px`,
            animationDelay: `${bubble.delay}s`,
            animationDuration: `${bubble.duration}s`,
            opacity: 0.6,
          }}
        >
          {/* Inner circle for depth */}
          <div 
            className="absolute inset-2 rounded-full bg-pink-300 opacity-30"
            style={{
              animation: `pulse ${bubble.duration * 0.7}s ease-in-out infinite`,
              animationDelay: `${bubble.delay}s`,
            }}
          />
        </div>
      ))}

      {/* Center loading content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {/* Main loading circle */}
        <div className="relative mb-8">
          <svg className="w-32 h-32 transform -rotate-90">
            {/* Background circle */}
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke="#e0e0e0"
              strokeWidth="4"
              fill="none"
              opacity="0.3"
            />
            {/* Progress circle */}
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke="url(#gradient)"
              strokeWidth="4"
              fill="none"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 56}`}
              strokeDashoffset={`${2 * Math.PI * 56 * (1 - progress / 100)}`}
              style={{
                transition: 'stroke-dashoffset 0.3s ease',
              }}
            />
            <defs>
              <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ec4899" />
                <stop offset="100%" stopColor="#f472b6" />
              </linearGradient>
            </defs>
          </svg>
          
          {/* Percentage in center */}
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-3xl font-bold text-pink-500">{progress}%</span>
          </div>
        </div>

        {/* Loading text */}
        <h2 className="text-2xl font-semibold text-gray-700 mb-2">Loading</h2>
        <p className="text-gray-500">Preparing your experience...</p>

        {/* Animated dots */}
        <div className="flex space-x-2 mt-6">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-3 h-3 rounded-full bg-pink-400"
              style={{
                animation: 'bounce 1.4s ease-in-out infinite',
                animationDelay: `${i * 0.2}s`,
              }}
            />
          ))}
        </div>
      </div>

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes float {
          0%, 100% {
            transform: translate(0, 0) scale(1);
          }
          25% {
            transform: translate(20px, -30px) scale(1.1);
          }
          50% {
            transform: translate(-15px, -50px) scale(1.2);
          }
          75% {
            transform: translate(25px, -35px) scale(1.15);
          }
        }

        @keyframes pulse {
          0%, 100% {
            transform: scale(0.8);
            opacity: 0.3;
          }
          50% {
            transform: scale(1.2);
            opacity: 0.5;
          }
        }

        @keyframes bounce {
          0%, 80%, 100% {
            transform: translateY(0);
          }
          40% {
            transform: translateY(-15px);
          }
        }

        .animate-float {
          animation: float 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
