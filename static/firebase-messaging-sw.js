// Firebase Service Worker for Push Notifications
importScripts('https://www.gstatic.com/firebasejs/12.7.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/12.7.0/firebase-messaging-compat.js');

// Initialize Firebase in Service Worker
firebase.initializeApp({
    apiKey: "AIzaSyDiMsHUyWyf3wk8SXbxeou2TlAr5D7GI4s",
    authDomain: "ibbt-5b0de.firebaseapp.com",
    projectId: "ibbt-5b0de",
    storageBucket: "ibbt-5b0de.firebasestorage.app",
    messagingSenderId: "956068448118",
    appId: "1:956068448118:web:08bb1418ae474d6e685c57"
});

const messaging = firebase.messaging();

// Handle background messages
messaging.onBackgroundMessage((payload) => {
    console.log('Background message received:', payload);

    const notificationTitle = payload.notification.title || 'إشعار جديد';
    const notificationOptions = {
        body: payload.notification.body || '',
        icon: '/static/icons/notification-icon.png',
        badge: '/static/icons/badge-icon.png',
        data: payload.data
    };

    self.registration.showNotification(notificationTitle, notificationOptions);
});

// Handle notification click
self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    // Get action URL from notification data
    const actionUrl = event.notification.data?.action_url || '/';

    event.waitUntil(
        clients.openWindow(actionUrl)
    );
});
