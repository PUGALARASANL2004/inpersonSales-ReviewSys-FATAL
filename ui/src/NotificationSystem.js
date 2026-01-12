import React from 'react'

// Notification Component
const Notification = ({ notification, onClose }) => {
  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return '✓'
      case 'error':
        return '✗'
      case 'warning':
        return '⚠'
      case 'info':
        return 'ℹ'
      default:
        return '•'
    }
  }

  const getColor = () => {
    switch (notification.type) {
      case 'success':
        return { bg: '#f0fdf4', border: '#22c55e', text: '#166534', icon: '#22c55e' }
      case 'error':
        return { bg: '#fef2f2', border: '#ef4444', text: '#991b1b', icon: '#ef4444' }
      case 'warning':
        return { bg: '#fffbeb', border: '#f59e0b', text: '#92400e', icon: '#f59e0b' }
      case 'info':
        return { bg: '#eff6ff', border: '#3b82f6', text: '#1e40af', icon: '#3b82f6' }
      default:
        return { bg: '#f9fafb', border: '#6b7280', text: '#374151', icon: '#6b7280' }
    }
  }

  const colors = getColor()

  return (
    <div
      style={{
        background: colors.bg,
        border: `2px solid ${colors.border}`,
        borderRadius: '8px',
        padding: '14px 16px',
        marginBottom: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        minWidth: '320px',
        maxWidth: '480px',
        animation: 'slideInRight 0.3s ease-out',
        position: 'relative'
      }}
    >
      <div
        style={{
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          background: colors.bg,
          border: `2px solid ${colors.icon}`,
          color: colors.icon,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '14px',
          fontWeight: 'bold',
          flexShrink: 0,
          marginTop: '2px'
        }}
      >
        {getIcon()}
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div
          style={{
            fontSize: '14px',
            fontWeight: 700,
            color: colors.text,
            marginBottom: '4px',
            lineHeight: '1.4'
          }}
        >
          {notification.title}
        </div>
        <div
          style={{
            fontSize: '13px',
            color: colors.text,
            opacity: 0.9,
            lineHeight: '1.5'
          }}
        >
          {notification.message}
        </div>
        <div
          style={{
            fontSize: '11px',
            color: colors.text,
            opacity: 0.7,
            marginTop: '6px'
          }}
        >
          {notification.timestamp.toLocaleTimeString()}
        </div>
      </div>
      <button
        onClick={() => onClose(notification.id)}
        style={{
          background: 'transparent',
          border: 'none',
          color: colors.text,
          cursor: 'pointer',
          fontSize: '18px',
          fontWeight: 'bold',
          padding: '0',
          width: '24px',
          height: '24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          opacity: 0.7,
          flexShrink: 0
        }}
        onMouseEnter={(e) => e.target.style.opacity = '1'}
        onMouseLeave={(e) => e.target.style.opacity = '0.7'}
      >
        ×
      </button>
      <style>{`
        @keyframes slideInRight {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      `}</style>
    </div>
  )
}

// Notification Container Component
export const NotificationContainer = ({ notifications, onClose }) => {
  if (notifications.length === 0) return null

  return (
    <div
      style={{
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: 10000,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-end',
        pointerEvents: 'none'
      }}
    >
      {notifications.map((notification) => (
        <div
          key={notification.id}
          style={{ pointerEvents: 'auto' }}
        >
          <Notification notification={notification} onClose={onClose} />
        </div>
      ))}
    </div>
  )
}

