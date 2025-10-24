import React, { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell
} from "recharts";

export default function TourismWeatherDashboard() {
  // States per visualization
  const [country, setCountry] = useState("All Countries");
  const [tourismData, setTourismData] = useState([]);
  const [countryOccupancy, setCountryOccupancy] = useState("All Countries");
  const [occupancyData, setOccupancyData] = useState([]);
  const [weatherCountry, setWeatherCountry] = useState("All Countries");
  const [weatherData, setWeatherData] = useState([]);
  const [destData, setDestData] = useState([]);
  const [seasonalData, setSeasonalData] = useState([]);

  const COLORS = ["#3B82F6", "#06B6D4", "#2563EB", "#60A5FA", "#1E40AF"];

  // Generic safe fetch function
  async function safeFetch(url, setter) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (Array.isArray(json)) setter(json);
      else setter([]);
    } catch (err) {
      console.warn(`⚠️ Failed to fetch ${url}:`, err.message);
      setter([]);
    }
  }

  // --- Fetch Tourism Trend Data ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/tourism?country=${country}`, setTourismData);
  }, [country]);

  // --- Fetch Hotel Occupancy Data ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/occupancy?country=${countryOccupancy}`, setOccupancyData);
  }, [countryOccupancy]);

  // --- Weather Impact on Bookings ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/weather-impact?country=${weatherCountry}`, setWeatherData);
  }, [weatherCountry]);

  // --- Top Destinations ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/top-destinations`, setDestData);
  }, []);

  // --- Seasonal Patterns ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/seasonal-patterns`, setSeasonalData);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-100 to-blue-200 p-6 text-slate-800">
      <header className="mb-6">
        <h1 className="text-4xl font-bold text-blue-700">Airbnb × Tourism Dashboard</h1>
        <p className="text-slate-600 mt-1">
          Explore how weather and tourism affect Airbnb activity across countries
        </p>
      </header>

      <main className="space-y-6">
        {/* --- 1. Tourism Trends --- */}
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-blue-700">Tourism Trends Over Time</h3>
            <select
              className="border border-blue-200 p-2 rounded-lg text-sm"
              value={country}
              onChange={(e) => setCountry(e.target.value)}
            >
              <option>All Countries</option>
              <option>Philippines</option>
              <option>Japan</option>
              <option>Thailand</option>
              <option>Indonesia</option>
              <option>Vietnam</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tourismData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="year" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="arrivals" stroke="#2563EB" />
            </LineChart>
          </ResponsiveContainer>
        </section>

        {/* --- 2. Country Occupancy --- */}
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-blue-700">Hotel Occupancy by Country</h3>
            <select
              className="border border-blue-200 p-2 rounded-lg text-sm"
              value={countryOccupancy}
              onChange={(e) => setCountryOccupancy(e.target.value)}
            >
              <option>All Countries</option>
              <option>Philippines</option>
              <option>Japan</option>
              <option>Thailand</option>
              <option>Indonesia</option>
              <option>Vietnam</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={occupancyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="country" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="occupancy" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </section>

        {/* --- 3. Weather Impact --- */}
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold text-blue-700">Weather Impact on Bookings</h3>
            <select
              className="border border-blue-200 p-2 rounded-lg text-sm"
              value={weatherCountry}
              onChange={(e) => setWeatherCountry(e.target.value)}
            >
              <option>All Countries</option>
              <option>Philippines</option>
              <option>Japan</option>
              <option>Thailand</option>
              <option>Indonesia</option>
            </select>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={weatherData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis yAxisId="left" orientation="left" stroke="#2563EB" />
              <YAxis yAxisId="right" orientation="right" stroke="#06B6D4" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="bookings" stroke="#2563EB" />
              <Line yAxisId="right" type="monotone" dataKey="rainfall" stroke="#06B6D4" />
            </LineChart>
          </ResponsiveContainer>
        </section>

        {/* --- 4. Top Destinations --- */}
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">Top Airbnb Destinations</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={destData}
                dataKey="value"
                nameKey="city"
                outerRadius={120}
                fill="#3B82F6"
                label
              >
                {destData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </section>

        {/* --- 5. Seasonal Patterns --- */}
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">Seasonal Travel Patterns</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={seasonalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="arrivals" fill="#2563EB" />
            </BarChart>
          </ResponsiveContainer>
        </section>
      </main>

      <footer className="mt-8 text-center text-sm text-blue-700 opacity-80">
        © 2025 Global Airbnb & Tourism Analytics — Understanding travel through data.
      </footer>
    </div>
  );
}
