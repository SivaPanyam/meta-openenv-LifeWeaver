import React from 'react';

export function NotificationPopup({ notification, onComplete, onExtend }) {
  if (!notification) return null;

  return (
    <div className="fixed top-6 right-6 z-50 animate-in fade-in slide-in-from-top-4 duration-300">
      <div className="bg-white border-2 border-indigo-600 rounded-xl shadow-2xl p-5 max-w-sm">
        <div className="flex items-start mb-4">
          <div className="bg-indigo-100 p-2 rounded-lg mr-3">
            <span className="text-2xl">🔔</span>
          </div>
          <div>
            <h4 className="font-bold text-gray-900">Event Check-in</h4>
            <p className="text-gray-600 text-sm mt-1">{notification.message}</p>
          </div>
        </div>
        
        <div className="flex space-x-3 mt-4">
          <button
            onClick={() => onComplete(notification.event)}
            className="flex-1 bg-indigo-600 text-white py-2 rounded-lg font-semibold hover:bg-indigo-700 transition-colors shadow-sm"
          >
            Yes, Completed
          </button>
          <button
            onClick={() => onExtend(notification.event)}
            className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-lg font-semibold hover:bg-gray-200 transition-colors"
          >
            Not Yet
          </button>
        </div>
      </div>
    </div>
  );
}
