import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import TourismWeatherDashboard from "./frontend"

function App() {
  const [count, setCount] = useState(0)

  return (
    <TourismWeatherDashboard />
  );
  
}

export default App
