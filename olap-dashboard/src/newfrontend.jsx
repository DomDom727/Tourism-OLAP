import React, { useState, useEffect } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from "recharts";

export default function AirbnbAnalyticsDashboard() {
  // State per visualization
  const [country, setCountry] = useState("All Countries");
  const [occupancyData, setOccupancyData] = useState([]);
  const [tempData, setTempData] = useState([]);
  const [typeData, setTypeData] = useState([]);
  const [ratingData, setRatingData] = useState([]);
  const [tourismData, setTourismData] = useState([]);

  const COLORS = ["#3B82F6", "#06B6D4", "#2563EB", "#60A5FA", "#1E40AF"];

  // Safe fetch helper
  async function safeFetch(url, setter) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      if (Array.isArray(json)) setter(json);
      else setter([]);
    } catch (err) {
      console.warn(`Failed to fetch ${url}:`, err.message);
      setter([]);
    }
  }

  // --- 1. Occupancy by Country ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/occupancy-by-country`, setOccupancyData);
  }, []);

  // --- 2. Occupancy vs Temperature ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/occupancy-vs-temp`, setTempData);
  }, []);

  // --- 3. Occupancy by Listing Type ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/occupancy-by-type`, setTypeData);
  }, []);

  // --- 4. Occupancy by Rating Band ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/occupancy-by-rating`, setRatingData);
  }, []);

  // --- 5. Tourism Trends ---
  useEffect(() => {
    safeFetch(`http://localhost:5000/api/tourism-rollup`, setTourismData);
  }, []);

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
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">
            Average Occupancy by Country and Month
          </h3>
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

        {/* --- 2. Occupancy vs Temperature --- */}
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">
            Occupancy vs. Average Temperature
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tempData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis yAxisId="left" orientation="left" stroke="#2563EB" />
              <YAxis yAxisId="right" orientation="right" stroke="#06B6D4" />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="avg_occupancy" stroke="#2563EB" />
              <Line yAxisId="right" type="monotone" dataKey="avg_temp" stroke="#06B6D4" />
            </LineChart>
          </ResponsiveContainer>
        </section>

        {/* --- 3. Occupancy by Listing Type --- */}
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">
            Occupancy by Listing Type and Country
          </h3>
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
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">
            Occupancy by Rating Band, Country, and Room Type
          </h3>
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
        <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow border border-blue-100">
          <h3 className="font-semibold text-blue-700 mb-3">
            Tourism Arrivals and Departures by Country and Year
          </h3>
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
