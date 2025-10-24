import React, { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";

export default function AirbnbAnalyticsDashboard() {
  // --- States ---
  const [countries, setCountries] = useState(["All Countries", "cambodia", "indonesia", "malaysia", "philippines", "singapore", "thailand", "vietnam"]);

  // Filters
  const [countryFilter1, setCountryFilter1] = useState("All Countries");
  const [countryFilter2, setCountryFilter2] = useState("All Countries");
  const [countryFilter3, setCountryFilter3] = useState("All Countries");
  const [countryFilter4, setCountryFilter4] = useState("All Countries");
  const [countryFilter5, setCountryFilter5] = useState("All Countries");

  // Data
  const [occupancyData, setOccupancyData] = useState([]);
  const [arrivalsData, setArrivalsData] = useState([]);
  const [typeData, setTypeData] = useState([]);
  const [ratingData, setRatingData] = useState([]);
  const [tourismData, setTourismData] = useState([]);

  // Colors
  const COLORS = ["#3B82F6", "#06B6D4", "#2563EB", "#60A5FA", "#1E40AF"];

  // Safe fetch helper
  async function safeFetch(url, setter) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setter(Array.isArray(json) ? json : []);
    } catch (err) {
      console.warn(`Failed to fetch ${url}:`, err.message);
      setter([]);
    }
  }

  // Load initial data
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/occupancy-by-country`, setOccupancyData);
    safeFetch(`http://localhost:5000/api/occupancy-vs-arrivals`, setArrivalsData);
    safeFetch(`http://localhost:5000/api/occupancy-by-type`, setTypeData);
    safeFetch(`http://localhost:5000/api/occupancy-by-rating`, setRatingData);
    safeFetch(`http://localhost:5000/api/tourism-rollup`, setTourismData);
  }, []);

  // --- Render ---
  return (
    <div className="min-h-screen bg-gradient-to-b from-indigo-50 to-blue-100 p-6 text-slate-800">
      <header className="mb-6">
        <h1 className="text-4xl font-bold text-blue-700">Airbnb OLAP Insights Dashboard</h1>
        <p className="text-slate-600 mt-1">
          Multidimensional insights from Airbnb and tourism data across countries
        </p>
      </header>

      <main className="space-y-6">

        {/* --- 1. Occupancy by Country --- */}
        <section className="bg-white/90 p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">Average Occupancy by Country and Month</h3>

          <div className="flex items-center gap-3 mb-4">
            <select
              className="border rounded-md px-3 py-1"
              value={countryFilter1}
              onChange={(e) => setCountryFilter1(e.target.value)}
            >
              {countries.map(c => <option key={c}>{c}</option>)}
            </select>
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
              onClick={() =>
                safeFetch(`http://localhost:5000/api/occupancy-by-country?country=${countryFilter1}`, setOccupancyData)
              }
            >
              Filter
            </button>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={occupancyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="avg_occupancy" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </section>

        {/* --- 2. Occupancy vs Arrivals --- */}
        <section className="bg-white/90 p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">Occupancy vs. Tourism Arrivals</h3>

          <div className="flex items-center gap-3 mb-4">
            <select
              className="border rounded-md px-3 py-1"
              value={countryFilter2}
              onChange={(e) => setCountryFilter2(e.target.value)}
            >
              {countries.map(c => <option key={c}>{c}</option>)}
            </select>
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
              onClick={() =>
                safeFetch(`http://localhost:5000/api/occupancy-vs-arrivals?country=${countryFilter2}`, setArrivalsData)
              }
            >
              Filter
            </button>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={arrivalsData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis yAxisId="left" orientation="left" stroke="#2563EB" />
              <YAxis yAxisId="right" orientation="right" stroke="#06B6D4" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="avg_occupancy" stroke="#2563EB" strokeWidth={2} />
              <Line yAxisId="right" type="monotone" dataKey="avg_arrivals" stroke="#06B6D4" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </section>

        {/* --- 3. Occupancy by Listing Type --- */}
        <section className="bg-white/90 p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">Occupancy by Listing Type and Country</h3>

          <div className="flex items-center gap-3 mb-4">
            <select
              className="border rounded-md px-3 py-1"
              value={countryFilter3}
              onChange={(e) => setCountryFilter3(e.target.value)}
            >
              {countries.map(c => <option key={c}>{c}</option>)}
            </select>
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
              onClick={() =>
                safeFetch(`http://localhost:5000/api/occupancy-by-type?country=${countryFilter3}`, setTypeData)
              }
            >
              Filter
            </button>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={typeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="country_name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="avg_occupancy" fill="#06B6D4" />
            </BarChart>
          </ResponsiveContainer>
        </section>

        {/* --- 4. Occupancy by Rating Band --- */}
        <section className="bg-white/90 p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">Occupancy by Rating Band, Country, and Room Type</h3>

          <div className="flex items-center gap-3 mb-4">
            <select
              className="border rounded-md px-3 py-1"
              value={countryFilter4}
              onChange={(e) => setCountryFilter4(e.target.value)}
            >
              {countries.map(c => <option key={c}>{c}</option>)}
            </select>
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
              onClick={() =>
                safeFetch(`http://localhost:5000/api/occupancy-by-rating?country=${countryFilter4}`, setRatingData)
              }
            >
              Filter
            </button>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={ratingData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="rating_group" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="avg_occupancy" fill="#60A5FA" />
            </BarChart>
          </ResponsiveContainer>
        </section>

        {/* --- 5. Tourism Trends --- */}
        <section className="bg-white/90 p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">Tourism Arrivals and Departures by Country and Year</h3>

          <div className="flex items-center gap-3 mb-4">
            <select
              className="border rounded-md px-3 py-1"
              value={countryFilter5}
              onChange={(e) => setCountryFilter5(e.target.value)}
            >
              {countries.map(c => <option key={c}>{c}</option>)}
            </select>
            <button
              className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
              onClick={() =>
                safeFetch(`http://localhost:5000/api/tourism-rollup?country=${countryFilter5}`, setTourismData)
              }
            >
              Filter
            </button>
          </div>

          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tourismData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="total_arrivals" stroke="#2563EB" />
              <Line type="monotone" dataKey="total_departures" stroke="#06B6D4" />
            </LineChart>
          </ResponsiveContainer>
        </section>
      </main>

      <footer className="mt-8 text-center text-sm text-blue-700 opacity-80">
        © 2025 Airbnb OLAP Analytics — Deep dives into occupancy, weather, and tourism data.
      </footer>
    </div>
  );
}
