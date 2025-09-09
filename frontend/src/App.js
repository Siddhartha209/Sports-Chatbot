import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import React, { useState } from "react";
import './theme.css';
import Home from "./pages/Home/Home";
import Navbar from './components/navbar/Navbar';

import "./App.css";
import PremierLeague from "./pages/pl/PremierLeague";

function App() {
  const [collapsed, setCollapsed] = useState(true);
  const [plMessages, setPLMessages] = useState([]);

  return (
    <Router>
      <Navbar collapsed={collapsed} setCollapsed={setCollapsed} />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/premier-league" element={<PremierLeague />} />
      </Routes>
    </Router>
  );
}

export default App;
