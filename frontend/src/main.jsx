import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { BrowserRouter } from "react-router-dom";
import store from './redux/store.jsx';
import {Provider} from "react-redux"
import { Toaster } from 'sonner';

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
    <Provider store={store}>
    <Toaster/>
    <App />
    </Provider>

    
    </BrowserRouter>
  </StrictMode>,
)
