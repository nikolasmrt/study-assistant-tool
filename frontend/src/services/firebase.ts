import { initializeApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
  apiKey: "AIzaSyAxkkS98XUmfBWRmxvUpIFW5P_3Zr-cdIA",
  authDomain: "study-assistant-nkn.firebaseapp.com",
  projectId: "study-assistant-nkn",
  storageBucket: "study-assistant-nkn.firebasestorage.app",
  messagingSenderId: "583034128846",
  appId: "1:583034128846:web:009ba0fc1861ebab74039f"
};


const app = initializeApp(firebaseConfig);


export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
export const db = getFirestore(app);