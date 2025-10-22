import React, { useState } from "react";

export default function TourismWeatherDashboard() {
  const [region, setRegion] = useState("All Regions");
  const [city, setCity] = useState("");
  const [startDate, setStartDate] = useState("2019-01-01");
  const [endDate, setEndDate] = useState("2024-12-31");
  const [metric, setMetric] = useState("arrivals");

  return (
    <div className="min-h-screen bg-gradient-to-b from-sky-100 to-blue-200 p-6 text-slate-800">
      <header className="mb-6">
        <h1 className="text-4xl font-bold text-blue-700">Philippines Tourism × Weather Dashboard</h1>
        <p className="text-slate-600 mt-1">Explore how weather affects tourism activity across the Philippines</p>
      </header>

      <div className="grid grid-cols-12 gap-6">
        <aside className="col-span-3 bg-white/80 backdrop-blur-sm p-4 rounded-2xl shadow-md border border-blue-100">
          <h2 className="font-semibold text-blue-700 mb-3">Filters</h2>
          <label className="block text-xs text-blue-600">Region</label>
          <select className="w-full p-2 rounded-lg border border-blue-200" value={region} onChange={(e) => setRegion(e.target.value)}>
            <option>All Regions</option>
            <option>National Capital Region (NCR)</option>
            <option>Ilocos Region (Region I)</option>
            <option>Cagayan Valley (Region II)</option>
            <option>Central Luzon (Region III)</option>
            <option>CALABARZON (Region IV-A)</option>
            <option>MIMAROPA (Region IV-B)</option>
            <option>Bicol Region (Region V)</option>
            <option>Western Visayas (Region VI)</option>
            <option>Central Visayas (Region VII)</option>
            <option>Eastern Visayas (Region VIII)</option>
            <option>Zamboanga Peninsula (Region IX)</option>
            <option>Northern Mindanao (Region X)</option>
            <option>Davao Region (Region XI)</option>
            <option>SOCCSKSARGEN (Region XII)</option>
            <option>Caraga (Region XIII)</option>
            <option>BANGSAMORO (BARMM)</option>
          </select>

          <label className="block text-xs text-blue-600 mt-3">City / Province</label>
          <input className="w-full p-2 rounded-lg border border-blue-200" placeholder="Optional city or province" value={city} onChange={(e) => setCity(e.target.value)} />

          <label className="block text-xs text-blue-600 mt-3">Start date</label>
          <input type="date" className="w-full p-2 rounded-lg border border-blue-200" value={startDate} onChange={(e) => setStartDate(e.target.value)} />

          <label className="block text-xs text-blue-600 mt-3">End date</label>
          <input type="date" className="w-full p-2 rounded-lg border border-blue-200" value={endDate} onChange={(e) => setEndDate(e.target.value)} />

          <label className="block text-xs text-blue-600 mt-3">Metric</label>
          <select className="w-full p-2 rounded-lg border border-blue-200" value={metric} onChange={(e) => setMetric(e.target.value)}>
            <option value="arrivals">Tourist Arrivals</option>
            <option value="occupancy">Hotel Occupancy</option>
            <option value="bookings">Airbnb Bookings</option>
            <option value="avg_price">Average Price</option>
          </select>

          <div className="mt-4 text-xs text-blue-500">
            <strong>Tip:</strong> Adjust filters to view tourism and weather data by region.
          </div>
        </aside>

        <main className="col-span-9 space-y-6">
          <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow-sm border border-blue-100">
            <h3 className="font-semibold text-blue-700 mb-2">Tourism Trends in the Philippines</h3>
            <div className="h-48 bg-gradient-to-r from-blue-100 to-sky-200 rounded-xl flex items-center justify-center text-blue-500 italic">
              Placeholder: Tourism growth and weather influence over time
            </div>
          </section>

          <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow-sm border border-blue-100">
            <h3 className="font-semibold text-blue-700 mb-2">Regional Tourist Arrivals</h3>
            <div className="h-48 bg-gradient-to-r from-blue-100 to-sky-200 rounded-xl flex items-center justify-center text-blue-500 italic">
              Placeholder: Tourist arrivals by Philippine region
            </div>
          </section>

          <section className="grid grid-cols-2 gap-4">
            <div className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow-sm border border-blue-100">
              <h3 className="font-semibold text-blue-700 mb-2">Weather Impact on Bookings</h3>
              <div className="h-56 bg-gradient-to-r from-blue-100 to-sky-200 rounded-xl flex items-center justify-center text-blue-500 italic">
                Placeholder: Correlation between temperature/rainfall and tourist demand
              </div>
            </div>

            <div className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow-sm border border-blue-100">
              <h3 className="font-semibold text-blue-700 mb-2">Top Tourist Destinations</h3>
              <div className="h-56 bg-gradient-to-r from-blue-100 to-sky-200 rounded-xl flex items-center justify-center text-blue-500 italic">
                Placeholder: Popular Philippine cities/provinces by tourist volume
              </div>
            </div>
          </section>

          <section className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow-sm border border-blue-100">
            <h3 className="font-semibold text-blue-700 mb-2">Seasonal Travel Patterns</h3>
            <div className="h-48 bg-gradient-to-r from-blue-100 to-sky-200 rounded-xl flex items-center justify-center text-blue-500 italic">
              Placeholder: Monthly and seasonal travel demand visualization
            </div>
          </section>
        </main>
      </div>

      <footer className="mt-8 text-center text-sm text-blue-700 opacity-80">
        © 2025 Philippines Tourism & Weather Analytics — Understanding our islands through data.
      </footer>
    </div>
  );
}
