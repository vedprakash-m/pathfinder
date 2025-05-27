import React from 'react';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation will be added here */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">Pathfinder</h1>
            </div>
            <div className="flex items-center space-x-4">
              {/* User menu will be added here */}
              <span className="text-sm text-gray-600">Welcome back!</span>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Main content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
};
