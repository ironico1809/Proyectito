importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.8.0/firebase-messaging-compat.js');

const firebaseConfig = {
  apiKey: "AIzaSyBo8Qvkg3KWDyMcrdf7toNWSdew-AePbFg",
  authDomain: "auxicar-project.firebaseapp.com",
  projectId: "auxicar-project",
  storageBucket: "auxicar-project.firebasestorage.app",
  messagingSenderId: "394292709586",
  appId: "1:394292709586:web:3df5b3a035404ebe63050b",
  measurementId: "G-5ZC05H340Z"
};

firebase.initializeApp(firebaseConfig);
const messaging = firebase.messaging();

messaging.onBackgroundMessage((payload) => {
  console.log('[firebase-messaging-sw.js] Received background message ', payload);
  const notificationTitle = payload.notification?.title || "Nueva Notificación";
  const notificationOptions = {
    body: payload.notification?.body || "",
    icon: '/favicon.ico',
    data: payload.data
  };

  self.registration.showNotification(notificationTitle, notificationOptions);
});
